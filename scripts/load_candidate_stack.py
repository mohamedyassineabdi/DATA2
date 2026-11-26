"""Load ignored, unvalidated candidates into a new isolated local Compose project.

The default mode only verifies required inputs. --apply requires explicit targets.
Never point this at the original Dalila Compose project or production services.
"""
import argparse
import collections
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from verify_local_workspace import digest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'local_only/data'
INPUTS = {
    'mariadb': DATA / 'original/sql/afi.sql',
    'postgis': DATA / 'processed/gis/candidates/candidates.jsonl',
    'fuseki': DATA / 'processed/knowledge_graph/candidate.ttl',
    'qdrant': DATA / 'processed/retrieval/chunks.jsonl',
}
RELATIONAL_INPUTS = {
    'zones': DATA / 'processed/relational/zones.jsonl',
    'lots': DATA / 'processed/relational/lots.jsonl',
}


def load_env(path):
    values = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip()
    return values


def compose(args, *command, data=None):
    cmd = ['docker', 'compose', '--env-file', str(args.env_file), '-f', str(ROOT / 'infrastructure/compose.yaml'), '-p', args.project, *command]
    result = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=900)
    if result.returncode:
        raise RuntimeError('Isolated Compose operation failed; inspect local service health without logging source records')
    return result.stdout.decode('utf-8', errors='replace').strip()


def sql_service(args, service, sql, *, input_bytes=None):
    if service == 'mariadb':
        cmd = ('sh', '-c', 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -uroot --batch --skip-column-names afi_restricted')
    else:
        cmd = ('sh', '-c', 'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -v ON_ERROR_STOP=1 -U dalila -d dalila_candidate -At')
    return compose(args, 'exec', '-T', service, *cmd, data=input_bytes if input_bytes is not None else sql.encode('utf-8'))


def qrequest(args, method, endpoint, payload=None, *, allow_404=False):
    key = args.secrets['QDRANT_API_KEY']
    port = args.secrets.get('QDRANT_PORT', '16333')
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(f'http://127.0.0.1:{port}{endpoint}', data=body, method=method,
                                 headers={'api-key': key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        raise RuntimeError(f'Qdrant returned HTTP {exc.code}') from None


def sparse_vector(text):
    terms = collections.Counter(t.casefold() for t in re.findall(r'[^\W_]+', text, flags=re.UNICODE))
    values = collections.Counter()
    for term, frequency in terms.items():
        index = int.from_bytes(hashlib.sha256(term.encode('utf-8')).digest()[:4], 'big') % 2147483647
        values[index] += frequency
    indices = sorted(values)
    return {'indices': indices, 'values': [float(values[index]) for index in indices]}


def verify_qdrant_ids(args, collection, expected):
    actual = set()
    offset = None
    while True:
        request = {'limit': 256, 'with_payload': False, 'with_vector': False}
        if offset is not None:
            request['offset'] = offset
        result = qrequest(args, 'POST', f'/collections/{collection}/points/scroll', request)['result']
        actual.update(point['id'] for point in result['points'])
        offset = result.get('next_page_offset')
        if offset is None:
            break
    if actual != expected:
        raise RuntimeError('Qdrant chunk IDs differ from the source corpus')
    return len(actual)


def verify_inputs():
    mapping = ROOT / 'local_only/audit/canonical_mapping.jsonl'
    expected = {}
    for line in mapping.open(encoding='utf-8'):
        item = json.loads(line)
        expected[item['local_path']] = item['sha256']
    result = {}
    for name, path in {**INPUTS, **RELATIONAL_INPUTS}.items():
        relative = path.relative_to(ROOT).as_posix()
        actual = digest(path)
        if expected.get(relative) != actual:
            raise RuntimeError(f'{name} checksum differs from canonical mapping')
        result[name] = {'sha256': actual, 'bytes': path.stat().st_size}
    return result


def load_mariadb(args):
    if sql_service(args, 'mariadb', 'SHOW TABLES;'):
        raise RuntimeError('MariaDB target is not empty; refusing to overwrite')
    with INPUTS['mariadb'].open('rb') as source:
        cmd = ['docker', 'compose', '--env-file', str(args.env_file), '-f', str(ROOT / 'infrastructure/compose.yaml'), '-p', args.project,
               'exec', '-T', 'mariadb', 'sh', '-c', 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -uroot afi_restricted']
        result = subprocess.run(cmd, stdin=source, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
    if result.returncode:
        raise RuntimeError('MariaDB import failed')
    tables = sql_service(args, 'mariadb', 'SHOW TABLES;').splitlines()
    counts = {name: int(sql_service(args, 'mariadb', f'SELECT COUNT(*) FROM `{name}`;')) for name in tables}
    if len(tables) != 13 or sum(counts.values()) != 15841:
        raise RuntimeError('MariaDB imported counts differ from frozen source inventory')
    return {'tables': len(tables), 'rows': sum(counts.values())}


def load_postgis(args):
    found = sql_service(args, 'postgis', "SELECT count(*) FROM information_schema.tables WHERE table_schema='candidate' AND table_name='geometry_source';")
    if found != '0':
        raise RuntimeError('PostGIS candidate table already exists; refusing to overwrite')
    statements = ["BEGIN; CREATE EXTENSION IF NOT EXISTS postgis; CREATE SCHEMA IF NOT EXISTS candidate; CREATE TABLE candidate.geometry_source (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, dataset_sha256 text NOT NULL, source_record jsonb NOT NULL, geom geometry, review_status text NOT NULL DEFAULT 'unvalidated'); CREATE TABLE candidate.zone_record (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, dataset_sha256 text NOT NULL, source_record jsonb NOT NULL, review_status text NOT NULL DEFAULT 'unvalidated'); CREATE TABLE candidate.lot_record (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, dataset_sha256 text NOT NULL, source_record jsonb NOT NULL, review_status text NOT NULL DEFAULT 'unvalidated');"]
    count = 0
    source_hash = digest(INPUTS['postgis'])
    with INPUTS['postgis'].open(encoding='utf-8') as source:
        for line in source:
            text = line.rstrip('\r\n').replace("'", "''")
            statements.append(f"INSERT INTO candidate.geometry_source(dataset_sha256,source_record) VALUES ('{source_hash}','{text}'::jsonb);")
            count += 1
    relational_counts = {}
    for family, path in RELATIONAL_INPUTS.items():
        table = 'zone_record' if family == 'zones' else 'lot_record'
        source_hash = digest(path)
        relational_counts[family] = 0
        with path.open(encoding='utf-8') as source:
            for line in source:
                text = line.rstrip('\r\n').replace("'", "''")
                statements.append(f"INSERT INTO candidate.{table}(dataset_sha256,source_record) VALUES ('{source_hash}','{text}'::jsonb);")
                relational_counts[family] += 1
    statements.append("UPDATE candidate.geometry_source SET geom=ST_SetSRID(ST_GeomFromGeoJSON((source_record->'geometry')::text),0) WHERE source_record->>'geometry_status'='candidate_valid' AND source_record->'geometry' IS NOT NULL AND source_record->'geometry' <> 'null'::jsonb; CREATE INDEX geometry_source_gix ON candidate.geometry_source USING gist (geom); CREATE INDEX zone_record_code_idx ON candidate.zone_record ((source_record->>'code_zone')); CREATE INDEX lot_record_zone_idx ON candidate.lot_record ((source_record->>'zone_id')); COMMIT;")
    sql_service(args, 'postgis', '\n'.join(statements))
    actual = int(sql_service(args, 'postgis', 'SELECT count(*) FROM candidate.geometry_source;'))
    assigned = int(sql_service(args, 'postgis', 'SELECT count(*) FROM candidate.geometry_source WHERE geom IS NOT NULL AND ST_SRID(geom)<>0;'))
    loaded_zones = int(sql_service(args, 'postgis', 'SELECT count(*) FROM candidate.zone_record;'))
    loaded_lots = int(sql_service(args, 'postgis', 'SELECT count(*) FROM candidate.lot_record;'))
    unmatched_lots = int(sql_service(args, 'postgis', "SELECT count(*) FROM candidate.lot_record l WHERE NOT EXISTS (SELECT 1 FROM candidate.zone_record z WHERE z.source_record->>'code_zone'=l.source_record->>'zone_id');"))
    if actual != count or assigned or loaded_zones != relational_counts['zones'] or loaded_lots != relational_counts['lots']:
        raise RuntimeError('PostGIS row count or zero-SRID boundary failed')
    return {'geometry_rows': actual, 'nonzero_srid_rows': assigned,
            'zones': loaded_zones, 'lots': loaded_lots, 'unmatched_lot_zone_references': unmatched_lots}


def load_fuseki(args):
    from base64 import b64encode
    port = args.secrets.get('FUSEKI_PORT', '13030')
    graph = 'urn:dalila:candidate:' + digest(INPUTS['fuseki'])[:16]
    url = f'http://127.0.0.1:{port}/candidate/data?graph=' + urllib.parse.quote(graph, safe='')
    credential = b64encode(('admin:' + args.secrets['FUSEKI_ADMIN_PASSWORD']).encode()).decode()
    headers = {'Authorization': 'Basic ' + credential, 'Content-Type': 'text/turtle'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers=headers), timeout=30) as response:
            if response.status == 200:
                raise RuntimeError('Candidate graph already exists; refusing to overwrite')
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise RuntimeError(f'Fuseki preflight returned HTTP {exc.code}') from None
    with INPUTS['fuseki'].open('rb') as stream:
        body = stream.read()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, method='PUT', headers=headers), timeout=300) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Fuseki graph load returned HTTP {exc.code}') from None
    return {'graph': graph, 'bytes': len(body), 'http_status': status}


def load_qdrant(args):
    path = INPUTS['qdrant']
    summary = json.loads((path.parent / 'summary.json').read_text(encoding='utf-8'))
    if digest(path) != summary['chunks_sha256']:
        raise RuntimeError('Chunk summary checksum mismatch')
    collection = 'dalila_candidate_lexical_' + summary['chunks_sha256'][:12]
    if qrequest(args, 'GET', '/collections/' + collection, allow_404=True) is not None:
        raise RuntimeError('Candidate Qdrant collection already exists; refusing to overwrite')
    config = {'vectors': {}, 'sparse_vectors': {'lexical': {'modifier': 'idf', 'index': {'on_disk': True}}},
              'metadata': {'chunks_sha256': summary['chunks_sha256'], 'review_status': 'unvalidated'}}
    qrequest(args, 'PUT', '/collections/' + collection, config)
    ids = set()
    batch = []
    with path.open(encoding='utf-8') as source:
        for line in source:
            chunk = json.loads(line)
            if chunk['review_status'] != 'unvalidated' or chunk['chunk_id'] in ids:
                raise RuntimeError('Chunk trust boundary or unique ID failed')
            ids.add(chunk['chunk_id'])
            batch.append({'id': chunk['chunk_id'], 'vector': {'lexical': sparse_vector(chunk['text'])},
                          'payload': {'chunk_id': chunk['chunk_id'], 'kind': chunk['kind'],
                                      'text_sha256': chunk['text_sha256'], 'review_status': 'unvalidated'}})
            if len(batch) == 64:
                qrequest(args, 'PUT', f'/collections/{collection}/points?wait=true', {'points': batch})
                batch = []
    if batch:
        qrequest(args, 'PUT', f'/collections/{collection}/points?wait=true', {'points': batch})
    count = qrequest(args, 'POST', f'/collections/{collection}/points/count', {'exact': True})['result']['count']
    if count != len(ids) or count != summary['chunk_count']:
        raise RuntimeError('Qdrant point count differs from source chunks')
    verified = verify_qdrant_ids(args, collection, ids)
    return {'collection': collection, 'points': count, 'ids_verified': verified, 'vector_type': 'lexical_sparse_only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / 'infrastructure/.env')
    parser.add_argument('--project', default='dalila-data2-local')
    parser.add_argument('--apply', action='store_true')
    for name in INPUTS:
        parser.add_argument('--' + name, action='store_true')
    args = parser.parse_args()
    verification = verify_inputs()
    targets = [name for name in INPUTS if getattr(args, name)]
    if not args.apply:
        print(json.dumps({'mode': 'verify_only', 'inputs': verification, 'requested_targets': targets}))
        return
    if not args.project.startswith('dalila-data2-') or not targets:
        parser.error('--apply requires explicit targets and a new dalila-data2-* project name')
    if not args.env_file.is_file():
        parser.error('Create a private infrastructure/.env from env.example')
    args.secrets = load_env(args.env_file)
    required = {'MARIADB_ROOT_PASSWORD', 'POSTGRES_PASSWORD', 'QDRANT_API_KEY', 'FUSEKI_ADMIN_PASSWORD'}
    if any(not args.secrets.get(key) or args.secrets[key].startswith('replace-with-') for key in required):
        parser.error('Replace all required placeholder secrets in the private environment file')
    results = {}
    for name in targets:
        results[name] = globals()['load_' + name](args)
    print(json.dumps({'mode': 'candidate_load', 'project': args.project, 'results': results}))


if __name__ == '__main__':
    main()

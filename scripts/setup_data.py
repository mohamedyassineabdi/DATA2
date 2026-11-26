"""Install DATA2 public tooling and, only with an authorized archive, local candidates.

This orchestrator never downloads the protected archive unless a caller supplies an
approved HTTPS URL and expected SHA-256. It never overwrites an installed corpus or
existing database target. Secrets and extracted source records stay in ignored paths.
"""
import argparse
import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import urllib.request
import urllib.parse
import zipfile
import zlib
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / 'local_only'
ENV = ROOT / 'infrastructure/.env'
DEFAULT_ARCHIVE_NAME = 'DATA2_local_candidate_v2.zip'
DEFAULT_ARCHIVE_SHA256 = '0addeb821a93e0d96bf40bc2edf893e184b221ec81d665cfbfc52514a3f0b1a2'
SERVICES = ('mariadb', 'postgis', 'fuseki', 'qdrant')
PORTS = {'MARIADB_PORT': 13316, 'POSTGIS_PORT': 15432,
         'FUSEKI_PORT': 13030, 'QDRANT_PORT': 16333}
MODES = ('complete', 'data-only', 'db-only', 'verify',
         'load-mariadb', 'load-postgis', 'load-fuseki', 'load-qdrant')


def run(command, *, env=None):
    subprocess.run([str(x) for x in command], cwd=ROOT, env=env, check=True)


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def verify_public():
    manifest = json.loads((ROOT / 'manifests/public_release.json').read_text(encoding='utf-8'))
    failures = []
    for item in manifest['files']:
        path = ROOT / item['path']
        if not path.is_file() or path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
            failures.append(item['path'])
    if failures or manifest['file_count'] != len(manifest['files']):
        raise RuntimeError(f'Public manifest verification failed for {len(failures)} files')
    return manifest['file_count']


def command_exists(name):
    return shutil.which(name) is not None


def python_in_venv():
    return ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def ensure_python(*, install):
    if sys.version_info < (3, 10):
        raise RuntimeError('Python 3.10 or newer is required')
    interpreter = python_in_venv()
    if not interpreter.is_file():
        if not install:
            raise RuntimeError('Missing .venv; run complete or data-only installation first')
        run([sys.executable, '-m', 'venv', ROOT / '.venv'])
    if install:
        pip = [interpreter, '-m', 'pip', 'install', '-r', ROOT / 'requirements.txt']
        try:
            run(pip)
        except subprocess.CalledProcessError:
            # No certificate bypass. pip 24 on some Windows hosts needs truststore.
            if os.name != 'nt':
                raise
            run([interpreter, '-m', 'pip', 'install', '--use-feature=truststore',
                 '-r', ROOT / 'requirements.txt'])
    return interpreter


def approved_download(url, expected):
    if not url.startswith('https://'):
        raise RuntimeError('Approved storage download must use HTTPS')
    target = LOCAL / 'transfer_pending' / DEFAULT_ARCHIVE_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        if sha256(target) != expected:
            raise RuntimeError('Existing archive hash differs; refusing overwrite')
        return target
    partial = target.with_suffix('.download-part')
    headers = {}
    token = os.environ.get('DATA2_ARCHIVE_BEARER_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    offset = partial.stat().st_size if partial.exists() else 0
    if offset:
        headers['Range'] = f'bytes={offset}-'
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        status = response.status
        content_range = response.headers.get('Content-Range', '')
        if offset and (status != 206 or not content_range.startswith(f'bytes {offset}-')):
            raise RuntimeError('Server did not honor the resumable Range request; partial file kept')
        with partial.open('ab' if offset else 'wb') as stream:
            while block := response.read(1024 * 1024):
                stream.write(block)
    if sha256(partial) != expected:
        raise RuntimeError('Downloaded archive SHA-256 mismatch; partial file kept for inspection')
    partial.replace(target)
    return target


def archive_expected_hash(path, provided):
    if provided:
        expected = provided.lower()
    elif path.name == DEFAULT_ARCHIVE_NAME:
        expected = DEFAULT_ARCHIVE_SHA256
    else:
        raise RuntimeError('A nonstandard archive requires --archive-sha256')
    if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
        raise RuntimeError('Expected SHA-256 must be 64 hexadecimal characters')
    return expected


def safe_members(archive):
    names = set()
    members = archive.infolist()
    if len(members) > 100000 or sum(item.file_size for item in members) > 10_000_000_000:
        raise RuntimeError('Archive exceeds bounded extraction limits')
    for item in members:
        name = item.filename
        p = PurePosixPath(name)
        if (name in names or name.startswith('/') or chr(92) in name or ':' in name or
                p.as_posix() != name or not p.parts or '..' in p.parts or
                p.parts[0] not in {'data', 'audit'} or item.is_dir() or
                (item.external_attr >> 16) & 0o170000 == 0o120000):
            raise RuntimeError('Archive has duplicate, unsafe or unsupported member')
        names.add(name)
    if 'audit/canonical_mapping.jsonl' not in names or 'audit/dataset_manifest.json' not in names:
        raise RuntimeError('Archive lacks the canonical mapping or dataset manifest')
    return members


def install_archive(path, expected):
    if not path.is_file() or sha256(path) != expected:
        raise RuntimeError('Archive missing or SHA-256 mismatch; nothing extracted')
    if (LOCAL / 'data').exists() or (LOCAL / 'audit').exists():
        if (LOCAL / 'data').is_dir() and (LOCAL / 'audit').is_dir():
            print('Protected corpus already installed; verifying existing files')
            return 'already_installed'
        raise RuntimeError('Partial local installation exists; inspect it before retrying')
    stage = LOCAL / '.setup-staging'
    stage.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        members = safe_members(archive)
        for item in members:
            output = stage.joinpath(*PurePosixPath(item.filename).parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.is_file() and output.stat().st_size == item.file_size:
                crc = 0
                with output.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        crc = zlib.crc32(block, crc)
                if crc & 0xffffffff == item.CRC:
                    continue
            temporary = output.with_name(output.name + '.setup-part')
            with archive.open(item) as source, temporary.open('wb') as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
            if temporary.stat().st_size != item.file_size:
                raise RuntimeError('Archive member size mismatch; staging retained')
            temporary.replace(output)
    mapping = stage / 'audit/canonical_mapping.jsonl'
    count = 0
    for line in mapping.open(encoding='utf-8'):
        item = json.loads(line)
        relative = PurePosixPath(item['local_path'])
        if relative.parts[:2] != ('local_only', 'data') or '..' in relative.parts:
            raise RuntimeError('Unsafe canonical mapping path')
        target = stage.joinpath(*relative.parts[1:])
        if not target.is_file() or target.stat().st_size != item['bytes'] or sha256(target) != item['sha256']:
            raise RuntimeError('Canonical mapping checksum failure; staging retained')
        count += 1
    dataset_manifest = json.loads((stage / 'audit/dataset_manifest.json').read_text(encoding='utf-8'))
    if count != dataset_manifest['source_file_mappings']:
        raise RuntimeError('Canonical mapping count differs from archive dataset manifest')
    data_count = sum(1 for p in (stage / 'data').rglob('*') if p.is_file())
    if data_count != dataset_manifest['dataset_count']:
        raise RuntimeError('Physical data file count differs from archive dataset manifest')
    (stage / 'data').replace(LOCAL / 'data')
    (stage / 'audit').replace(LOCAL / 'audit')
    stage.rmdir()
    return 'installed'


def free_port(port):
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def choose_port(preferred, chosen):
    for port in range(preferred, preferred + 100):
        if port not in chosen and free_port(port):
            chosen.add(port)
            return port
    raise RuntimeError(f'No free loopback port near {preferred}')


def ensure_env():
    if ENV.exists():
        values = dict(line.split('=', 1) for line in ENV.read_text(encoding='utf-8').splitlines()
                      if '=' in line and not line.startswith('#'))
        if any(not values.get(k) or values[k].startswith('replace-with-') for k in
               ('MARIADB_ROOT_PASSWORD', 'POSTGRES_PASSWORD', 'FUSEKI_ADMIN_PASSWORD', 'QDRANT_API_KEY')):
            raise RuntimeError('Existing .env has placeholder secrets; edit it locally')
        return values, False
    selected = set()
    values = {key: str(choose_port(port, selected)) for key, port in PORTS.items()}
    for key in ('MARIADB_ROOT_PASSWORD', 'POSTGRES_PASSWORD', 'FUSEKI_ADMIN_PASSWORD',
                'QDRANT_API_KEY', 'FUSEKI_CANDIDATE_PASSWORD',
                'REDIS_COORDINATION_PASSWORD', 'SQL_CANDIDATE_READ_PASSWORD'):
        values[key] = secrets.token_urlsafe(32)
    ENV.write_text(''.join(f'{key}={value}\n' for key, value in values.items()), encoding='utf-8')
    ENV.chmod(0o600)
    return values, True


def compose(project, *args):
    run(['docker', 'compose', '--env-file', ENV, '-f', ROOT / 'infrastructure/compose.yaml',
         '-p', project, *args])


def existing_state(project, service, env):
    sys.path.insert(0, str(ROOT / 'scripts'))
    import load_candidate_stack as loader
    args = argparse.Namespace(project=project, env_file=ENV, secrets=env)
    if service == 'mariadb':
        names = loader.sql_service(args, service, 'SHOW TABLES;').splitlines()
        if not names:
            return 'absent'
        counts = [int(loader.sql_service(args, service, f'SELECT COUNT(*) FROM `{name}`;')) for name in names]
        return 'complete' if len(names) == 13 and sum(counts) == 15841 else 'partial'
    if service == 'postgis':
        found = loader.sql_service(args, service, "SELECT count(*) FROM information_schema.tables WHERE table_schema='candidate' AND table_name='geometry_source';")
        if found == '0':
            return 'absent'
        query = "SELECT (SELECT count(*) FROM candidate.geometry_source),(SELECT count(*) FROM candidate.zone_record),(SELECT count(*) FROM candidate.lot_record),(SELECT count(*) FROM candidate.geometry_source WHERE geom IS NOT NULL AND ST_SRID(geom)<>0);"
        return 'complete' if loader.sql_service(args, service, query) == '12006|185|6579|0' else 'partial'
    if service == 'qdrant':
        corpus = loader.INPUTS['qdrant']
        collection = 'dalila_candidate_lexical_' + sha256(corpus)[:12]
        info = loader.qrequest(args, 'GET', '/collections/' + collection, allow_404=True)
        if info is None:
            return 'absent'
        count = loader.qrequest(args, 'POST', f'/collections/{collection}/points/count', {'exact': True})['result']['count']
        if count != 10381:
            return 'partial'
        with corpus.open(encoding='utf-8') as source:
            expected_ids = {json.loads(line)['chunk_id'] for line in source}
        return 'complete' if loader.verify_qdrant_ids(args, collection, expected_ids) == 10381 else 'partial'
    if service == 'fuseki':
        import base64
        import urllib.error
        graph = 'urn:dalila:candidate:' + sha256(loader.INPUTS['fuseki'])[:16]
        url = (f"http://127.0.0.1:{env['FUSEKI_PORT']}/candidate/data?graph=" +
               urllib.parse.quote(graph, safe=''))
        credential = base64.b64encode(('admin:' + env['FUSEKI_ADMIN_PASSWORD']).encode()).decode()
        request = urllib.request.Request(url, method='HEAD', headers={'Authorization': 'Basic ' + credential})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    return 'partial'
            query = f'SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{graph}> {{ ?s ?p ?o }} }}'
            query_url = (f"http://127.0.0.1:{env['FUSEKI_PORT']}/candidate/query?" +
                         urllib.parse.urlencode({'query': query}))
            query_request = urllib.request.Request(query_url, headers={
                'Authorization': 'Basic ' + credential, 'Accept': 'application/sparql-results+json'})
            with urllib.request.urlopen(query_request, timeout=60) as response:
                count = int(json.load(response)['results']['bindings'][0]['n']['value'])
            return 'complete' if count == 93495 else 'partial'
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return 'absent'
            raise
    raise ValueError(service)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=MODES, default='complete')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--archive-sha256')
    parser.add_argument('--archive-url')
    parser.add_argument('--project', default='dalila-data2-local')
    parser.add_argument('--with-redis', action='store_true')
    parser.add_argument('--skip-dependencies', action='store_true')
    args = parser.parse_args(argv)
    if not args.project.startswith('dalila-data2-'):
        parser.error('Project must start with dalila-data2- to isolate candidate services')
    public_count = verify_public()
    if args.archive and args.archive_url:
        parser.error('Choose a local archive or approved HTTPS URL, not both')
    if args.mode == 'verify' and (args.archive or args.archive_url):
        parser.error('Verification mode does not install an archive')
    if args.archive or args.archive_url:
        expected = archive_expected_hash(args.archive or Path(DEFAULT_ARCHIVE_NAME), args.archive_sha256)
        archive = args.archive or approved_download(args.archive_url, expected)
        status = install_archive(archive.resolve(), expected)
        print(json.dumps({'archive_status': status, 'sha256': expected}))
    have_data = (LOCAL / 'data').is_dir() and (LOCAL / 'audit').is_dir()
    need_dependencies = args.mode in ('complete', 'data-only') and not args.skip_dependencies
    interpreter = (ensure_python(install=need_dependencies)
                   if need_dependencies or (have_data and args.mode != 'db-only') else None)
    if have_data and args.mode != 'db-only':
        run([interpreter, ROOT / 'scripts/verify_local_workspace.py'])
        run([interpreter, ROOT / 'scripts/verify_candidate_data.py'])
        run([interpreter, ROOT / 'scripts/load_candidate_stack.py'])
    elif not have_data and args.mode == 'data-only':
        raise RuntimeError('Protected candidate corpus is absent; supply an authorized archive')
    if not have_data and args.mode.startswith('load-'):
        raise RuntimeError('Cannot load a database without an authorized candidate corpus')
    need_db = args.mode in ('complete', 'db-only') or args.mode.startswith('load-')
    summary = {'mode': args.mode, 'public_manifest_files': public_count,
               'protected_corpus': 'verified' if have_data and args.mode != 'db-only' else
               ('present_not_checked' if have_data else 'absent'), 'project': args.project}
    if need_db and have_data or args.mode == 'db-only':
        if not command_exists('docker'):
            raise RuntimeError('Docker and Docker Compose are required for database modes')
        run(['docker', 'compose', 'version'])
        env, created = ensure_env()
        if created:
            summary['new_credentials'] = 'generated in ignored infrastructure/.env'
        targets = SERVICES if args.mode == 'complete' else (() if args.mode == 'db-only' else (args.mode.removeprefix('load-'),))
        start = targets or SERVICES
        compose(args.project, 'up', '-d', '--wait', *start)
        if args.with_redis:
            acl = ROOT / 'infrastructure/redis-users.local.acl'
            if not acl.is_file():
                run([sys.executable, ROOT / 'scripts/prepare_redis_acl.py'], env={**os.environ, **env})
            compose(args.project, '--profile', 'coordination', 'up', '-d', '--wait', 'redis')
        states = {}
        for service in targets:
            state = existing_state(args.project, service, env)
            if state == 'partial':
                raise RuntimeError(f'{service} target is partial or unexpected; refusing overwrite')
            if state == 'absent':
                run([interpreter, ROOT / 'scripts/load_candidate_stack.py', '--apply',
                     '--project', args.project, '--env-file', ENV, '--' + service])
                state = existing_state(args.project, service, env)
                if state != 'complete':
                    raise RuntimeError(f'{service} import did not pass completion check')
            states[service] = state
        summary['database_targets'] = states
        if args.mode == 'complete':
            run([interpreter, ROOT / 'scripts/query_candidate_stack.py', '--project', args.project,
                 '--env-file', ENV])
            summary['database_queries'] = 'passed'
        elif args.mode == 'db-only':
            summary['database_targets'] = 'initialized_empty_no_import'
    elif need_db:
        summary['database_targets'] = 'skipped_no_authorized_corpus'
    elif args.mode == 'verify' and have_data and ENV.is_file() and command_exists('docker'):
        env, _ = ensure_env()
        try:
            states = {service: existing_state(args.project, service, env) for service in SERVICES}
            summary['database_targets'] = states
            if all(state == 'complete' for state in states.values()):
                run([interpreter, ROOT / 'scripts/query_candidate_stack.py', '--project', args.project,
                     '--env-file', ENV])
                summary['database_queries'] = 'passed'
        except (subprocess.CalledProcessError, RuntimeError, OSError) as exc:
            summary['database_targets'] = 'not_running_or_unreachable'
    if not have_data and args.mode == 'complete':
        summary['installation'] = 'public_only; obtain authorized archive for actual data and databases'
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError, zipfile.BadZipFile) as exc:
        print(f'DATA2 setup stopped safely: {exc}', file=sys.stderr)
        raise SystemExit(1) from None

"""Run aggregate read-only smoke queries against an isolated candidate stack."""
import argparse
import base64
import json
import urllib.parse
import urllib.request
from pathlib import Path

from load_candidate_stack import ROOT, INPUTS, digest, load_env, qrequest, sparse_vector, sql_service


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / 'infrastructure/.env')
    parser.add_argument('--project', default='dalila-data2-local')
    args = parser.parse_args()
    if not args.project.startswith('dalila-data2-'):
        parser.error('Only isolated dalila-data2-* projects are supported')
    args.secrets = load_env(args.env_file)
    lots = int(sql_service(args, 'mariadb', 'SELECT COUNT(*) FROM lots;'))
    postgis = sql_service(args, 'postgis', 'SELECT count(*),count(geom),count(*) FILTER (WHERE geom IS NOT NULL AND ST_SRID(geom)<>0) FROM candidate.geometry_source;')
    graph = 'urn:dalila:candidate:' + digest(INPUTS['fuseki'])[:16]
    query = f'SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{graph}> {{ ?s ?p ?o }} }}'
    auth = base64.b64encode(('admin:' + args.secrets['FUSEKI_ADMIN_PASSWORD']).encode()).decode()
    port = args.secrets.get('FUSEKI_PORT', '13030')
    url = f'http://127.0.0.1:{port}/candidate/query?' + urllib.parse.urlencode({'query': query})
    request = urllib.request.Request(url, headers={'Authorization': 'Basic ' + auth, 'Accept': 'application/sparql-results+json'})
    with urllib.request.urlopen(request, timeout=60) as response:
        triples = int(json.load(response)['results']['bindings'][0]['n']['value'])
    collection = 'dalila_candidate_lexical_' + digest(INPUTS['qdrant'])[:12]
    result = qrequest(args, 'POST', f'/collections/{collection}/points/query',
                      {'query': sparse_vector('zone industrielle'), 'using': 'lexical',
                       'limit': 3, 'with_payload': False})
    print(json.dumps({'mariadb_lots': lots, 'postgis_rows_geom_nonzero_srid': postgis,
                      'fuseki_candidate_triples': triples,
                      'qdrant_sample_results': len(result['result']['points']),
                      'knowledge_status': 'unvalidated_candidate'}))


if __name__ == '__main__':
    main()

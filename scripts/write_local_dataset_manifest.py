"""Summarize every protected canonical file and its original source paths."""
import json
from collections import defaultdict
from pathlib import Path


root = Path(__file__).resolve().parents[1]
mapping = root / 'local_only/audit/canonical_mapping.jsonl'
by_path = defaultdict(list)
for line in mapping.open(encoding='utf-8'):
    item = json.loads(line)
    by_path[item['local_path']].append(item)
datasets = []
for local_path, sources in sorted(by_path.items()):
    first = sources[0]
    datasets.append({'path': local_path, 'format': first['format'], 'bytes': first['bytes'],
                     'sha256': first['sha256'], 'record_count': first['record_count'],
                     'source_paths': [s['source_path'] for s in sources],
                     'validation_status': 'candidate_or_original_unreviewed',
                     'sharing_status': 'LOCAL_ONLY_NO_EXTERNAL_TRANSFER'})
manifest = {'schema_version': '1', 'dataset_count': len(datasets),
            'source_file_mappings': sum(len(s) for s in by_path.values()),
            'original_frozen_release_preserved': True, 'datasets': datasets}
target = root / 'local_only/audit/dataset_manifest.json'
target.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'canonical_files': manifest['dataset_count'], 'source_file_mappings': manifest['source_file_mappings']}))

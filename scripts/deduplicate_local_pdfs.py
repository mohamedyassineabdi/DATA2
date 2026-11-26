"""Drop only exact duplicate local PDF copies; keep all original source paths."""
import json
from pathlib import Path
from verify_local_workspace import digest
from build_local_workspace import CANONICAL


root = Path(__file__).resolve().parents[1]
mapping_path = root / 'local_only/audit/canonical_mapping.jsonl'
rows = [json.loads(line) for line in mapping_path.open(encoding='utf-8')]
first = {}
removed = 0
for row in rows:
    if row['format'] != 'pdf':
        continue
    if row.get('exact_duplicate_of'):
        for prefix, target in CANONICAL.items():
            if row['source_path'].startswith(prefix + '/'):
                former = (root / 'local_only/data' / target / row['source_path'][len(prefix) + 1:]).resolve()
                if former != (root / row['exact_duplicate_of']).resolve() and former.is_relative_to(root / 'local_only/data/original') and former.is_file() and digest(former) == row['sha256']:
                    former.unlink()
                    removed += 1
                break
        continue
    current = (root / row['local_path']).resolve()
    key = row['sha256']
    if key not in first:
        first[key] = row['local_path']
        continue
    if current.is_relative_to(root / 'local_only/data/original') and current.is_file() and digest(current) == key and row['local_path'] != first[key]:
        current.unlink()
        removed += 1
    row['local_path'] = first[key]
    row['exact_duplicate_of'] = first[key]
with mapping_path.open('w', encoding='utf-8') as stream:
    for row in rows:
        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
print(json.dumps({'unique_pdf_sha256': len(first), 'duplicate_copies_removed': removed}))

"""List reversible cleanup candidates; never delete the original workspace."""
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
audit = root / 'local_only/audit'
inventory = [json.loads(line) for line in (audit / 'full_inventory.jsonl').open(encoding='utf-8')]
mapped = {json.loads(line)['source_path'] for line in (audit / 'canonical_mapping.jsonl').open(encoding='utf-8')}
first_hash = {}
output = audit / 'cleanup_candidates.jsonl'
counts = {'exact_duplicate_paths': 0, 'not_selected_for_canonical_copy': 0}
with output.open('w', encoding='utf-8') as stream:
    for item in inventory:
        old = first_hash.setdefault(item['sha256'], item['source_path'])
        if old != item['source_path']:
            reason = 'exact_duplicate_bytes'
            counts['exact_duplicate_paths'] += 1
        elif item['source_path'] not in mapped:
            reason = 'not_selected_for_canonical_copy'
            counts['not_selected_for_canonical_copy'] += 1
        else:
            continue
        stream.write(json.dumps({'source_path': item['source_path'], 'reason': reason,
                                 'retained_reference': old if reason == 'exact_duplicate_bytes' else None,
                                 'action': 'retain_original_pending_manual_cleanup_review'}, ensure_ascii=False) + '\n')
print(json.dumps(counts))

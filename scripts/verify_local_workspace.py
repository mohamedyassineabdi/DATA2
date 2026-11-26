"""Verify the protected local consolidation without printing source content."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    a = p.parse_args()
    root = a.root.resolve()
    mapping = root / 'local_only/audit/canonical_mapping.jsonl'
    if not mapping.is_file():
        raise SystemExit('Protected local candidate copy is absent; obtain an authorized source transfer first')
    counts = Counter()
    failed = []
    for line in mapping.open(encoding='utf-8'):
        item = json.loads(line)
        path = (root / item['local_path']).resolve()
        if not path.is_relative_to(root / 'local_only') or not path.is_file() or path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            failed.append(item['local_path'])
        counts['files'] += 1
        counts['bytes'] += item['bytes']
        if path.suffix.lower() == '.pdf':
            counts['pdfs'] += 1
    print(json.dumps({**counts, 'failed': len(failed), 'status': 'pass' if not failed else 'fail'}, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

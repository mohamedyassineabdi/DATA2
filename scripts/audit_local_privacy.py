"""Aggregate local privacy indicators without printing or exporting source text."""
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'local_only/data'
EMAIL = re.compile(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b')
TOKEN = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|Bearer\s+[A-Za-z0-9_.-]{20,})')


def screen_text(value, counts, family):
    if EMAIL.search(value):
        counts[family + '_records_with_email_shape'] += 1
    if TOKEN.search(value):
        counts[family + '_records_with_credential_shape'] += 1


def main():
    import pymupdf

    counts = Counter()
    pdfs = list((DATA / 'original').rglob('*.pdf'))
    for path in pdfs:
        found_email = False
        found_token = False
        with pymupdf.open(path) as pdf:
            for page in pdf:
                text = page.get_text()
                found_email |= bool(EMAIL.search(text))
                found_token |= bool(TOKEN.search(text))
        counts['pdfs_screened'] += 1
        counts['pdfs_with_email_shape'] += found_email
        counts['pdfs_with_credential_shape'] += found_token
    sql = (DATA / 'original/sql/afi.sql').read_text(encoding='utf-8', errors='replace')
    counts['sql_email_shape_occurrences'] = len(EMAIL.findall(sql))
    counts['sql_credential_shape_occurrences'] = len(TOKEN.findall(sql))
    paths = {
        'ocr': (DATA / 'processed/ocr/best/pages', 'text', '*.json'),
        'articles': (DATA / 'processed/regulations_and_institutional/article_candidates.jsonl', 'original_text_candidate', None),
        'passages': (DATA / 'processed/regulations_and_institutional/institutional_passages.jsonl', 'passage', None),
        'chunks': (DATA / 'processed/retrieval/chunks.jsonl', 'text', None),
        'institutional_pages': (DATA / 'processed/institutional/pages/pages.jsonl', 'text', None),
        'structured_web': (DATA / 'processed/institutional/structured/candidates.jsonl', 'text', None),
    }
    for family, (path, field, glob) in paths.items():
        if glob:
            values = (json.loads(p.read_text(encoding='utf-8')) for p in path.glob(glob))
        else:
            values = (json.loads(line) for line in path.open(encoding='utf-8'))
        for row in values:
            counts[family + '_records_screened'] += 1
            screen_text(str(row.get(field, '')), counts, family)
    result = {'status': 'heuristic_screen_only_no_publication_clearance',
              'counts': dict(counts),
              'limitations': ['An email shape may be an official public contact, not private information.',
                              'Names, scanned handwriting and licensed third-party content require human review.',
                              'Absence of pattern matches does not establish redistribution rights.']}
    target = ROOT / 'local_only/audit/privacy_screen.json'
    target.write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({'pdfs_screened': counts['pdfs_screened'],
                      'candidate_records_screened': sum(value for key, value in counts.items() if key.endswith('_records_screened')),
                      'flagged_families': sorted(key for key, value in counts.items() if value and ('email_shape' in key or 'credential_shape' in key))}))


if __name__ == '__main__':
    main()

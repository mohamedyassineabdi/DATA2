"""Structural audit of the ignored, unvalidated local candidate corpus."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from verify_local_workspace import digest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'local_only/data'


def rows(relative):
    with (DATA / relative).open(encoding='utf-8') as stream:
        for number, line in enumerate(stream, 1):
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSONL at {relative}:{number}') from exc


def main():
    import pymupdf
    from rdflib import Graph
    from shapely.geometry import shape

    pdfs = list((DATA / 'original').rglob('*.pdf'))
    pdf_pages = {}
    for path in pdfs:
        with pymupdf.open(path) as document:
            pdf_pages[digest(path)] = len(document)
    ocr = [json.loads(path.read_text(encoding='utf-8')) for path in (DATA / 'processed/ocr/best/pages').glob('*.json')]
    ocr_pairs = {(r['source_sha256'], r['page']) for r in ocr}
    article = list(rows('processed/regulations_and_institutional/article_candidates.jsonl'))
    passage = list(rows('processed/regulations_and_institutional/institutional_passages.jsonl'))
    chunks = list(rows('processed/retrieval/chunks.jsonl'))
    zones = list(rows('processed/relational/zones.jsonl'))
    lots = list(rows('processed/relational/lots.jsonl'))
    gis = list(rows('processed/gis/candidates/candidates.jsonl'))
    pages = list(rows('processed/institutional/pages/pages.jsonl'))
    structured = list(rows('processed/institutional/structured/candidates.jsonl'))
    zone_ids = {str(z.get('code_zone')) for z in zones}
    article_pairs = {(a['document_sha256'], a['source_page']) for a in article}
    errors = Counter()
    errors['duplicate_ocr_page_key'] = len(ocr) - len(ocr_pairs)
    errors['ocr_text_hash_mismatch'] = sum(hashlib.sha256(r['text'].encode('utf-8')).hexdigest() != r['text_sha256'] for r in ocr)
    errors['ocr_missing_pdf'] = sum(r['source_sha256'] not in pdf_pages for r in ocr)
    errors['ocr_page_out_of_range'] = sum(r['page'] < 1 or r['page'] > pdf_pages.get(r['source_sha256'], 0) for r in ocr)
    errors['article_missing_pdf'] = sum(a['document_sha256'] not in pdf_pages for a in article)
    errors['article_page_out_of_range'] = sum(a['source_page'] < 1 or a['source_page'] > pdf_pages.get(a['document_sha256'], 0) for a in article)
    errors['ocr_article_without_checkpoint'] = sum(a.get('extraction_method') != 'native_text' and (a['document_sha256'], a['source_page']) not in ocr_pairs for a in article)
    errors['article_chunk_without_article_page'] = sum(c['kind'] == 'article_candidate' and (c['document_sha256'], c['source_page']) not in article_pairs for c in chunks)
    errors['chunk_text_hash_mismatch'] = sum(hashlib.sha256(c['text'].encode('utf-8')).hexdigest() != c['text_sha256'] for c in chunks)
    errors['duplicate_chunk_id'] = len(chunks) - len({c['chunk_id'] for c in chunks})
    flags = Counter()
    flags['native_articles_without_ocr_checkpoint'] = sum(a.get('extraction_method') == 'native_text' and (a['document_sha256'], a['source_page']) not in ocr_pairs for a in article)
    flags['lots_with_unknown_zone'] = sum(str(l.get('zone_id')) not in zone_ids for l in lots)
    for item in gis:
        geometry = item.get('geometry')
        if geometry:
            try:
                parsed = shape(geometry)
                if not parsed.is_valid:
                    flags['invalid_geometries'] += 1
            except Exception:
                flags['unparseable_geometries'] += 1
        else:
            flags['missing_geometries'] += 1
    graph = Graph().parse(DATA / 'processed/knowledge_graph/candidate.ttl', format='turtle')
    json_files = [path for path in DATA.rglob('*') if path.is_file() and path.suffix.lower() in {'.json', '.jsonl'}]
    for path in json_files:
        with path.open(encoding='utf-8-sig') as stream:
            if path.suffix.lower() == '.json':
                json.load(stream)
            else:
                for line in stream:
                    if line.strip():
                        json.loads(line)
    csv_files = list(DATA.rglob('*.csv'))
    for path in csv_files:
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for _ in csv.reader(stream):
                pass
    result = {'pdfs': len(pdfs), 'pdf_pages': sum(pdf_pages.values()), 'ocr_checkpoints': len(ocr),
              'articles': len(article), 'passages': len(passage), 'chunks': len(chunks),
              'zones': len(zones), 'lots': len(lots), 'gis_candidates': len(gis),
              'institutional_pages': len(pages), 'structured_web_candidates': len(structured),
              'rdf_triples': len(graph), 'json_jsonl_files_parsed': len(json_files),
              'csv_files_parsed': len(csv_files), 'structural_errors': dict(errors),
              'unvalidated_quality_flags': dict(flags)}
    target = ROOT / 'local_only/audit/structural_integrity.json'
    target.write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(result))
    if any(errors.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()

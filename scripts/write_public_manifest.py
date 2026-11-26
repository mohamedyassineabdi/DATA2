"""Record exact public release bytes; source-bearing local_only is never included."""
import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
allowed = ('README.md', 'DATA_STATUS.md', '.gitignore', '.gitattributes', 'ontology', 'schemas', 'infrastructure', 'scripts', 'tests', 'docs')
files = []
for name in allowed:
    base = root / name
    for path in ([base] if base.is_file() else base.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith('local_only/'):
            raise RuntimeError('Local-only file escaped into public manifest')
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': h})
files.sort(key=lambda x: x['path'])
manifest = {'schema_version': '1', 'release_kind': 'public_tooling_and_synthetic_drafts',
            'source_bearing_datasets_included': False, 'validation_status': 'no_validated_knowledge',
            'files': files, 'file_count': len(files), 'total_bytes': sum(item['bytes'] for item in files)}
target = root / 'manifests/public_release.json'
target.parent.mkdir(exist_ok=True)
target.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'file_count': manifest['file_count'], 'total_bytes': manifest['total_bytes']}))

"""Record exact public release bytes; private local files are never included."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED = ('README.md', 'DATA_STATUS.md', 'requirements.txt', 'setup_data.ps1', 'setup_data.sh',
           '.gitignore', '.gitattributes',
           'ontology', 'schemas', 'infrastructure', 'scripts', 'tests', 'docs', 'manifests')


def is_public_file(path):
    return (path.is_file()
            and not any(part in {'.git', '.venv', 'local_only', '__pycache__'} for part in path.parts)
            and path.suffix not in {'.pyc', '.key', '.pem', '.p12', '.pfx', '.acl'}
            and not path.name.startswith('.env')
            and path.name not in {'public_release.json', 'checksums.sha256'})


def main():
    files = []
    for name in ALLOWED:
        base = ROOT / name
        for path in ([base] if base.is_file() else base.rglob('*')):
            if not is_public_file(path):
                continue
            relative = path.relative_to(ROOT).as_posix()
            files.append({'path': relative, 'bytes': path.stat().st_size,
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    files.sort(key=lambda item: item['path'])
    manifest = {'schema_version': '1', 'release_kind': 'public_tooling_and_synthetic_drafts',
                'source_bearing_datasets_included': False, 'validation_status': 'no_validated_knowledge',
                'files': files, 'file_count': len(files), 'total_bytes': sum(item['bytes'] for item in files)}
    target = ROOT / 'manifests/public_release.json'
    target.parent.mkdir(exist_ok=True)
    target.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    (ROOT / 'manifests/checksums.sha256').write_bytes((''.join(item['sha256'] + '  ' + item['path'] + '\n' for item in files)).encode('utf-8'))
    print(json.dumps({'file_count': manifest['file_count'], 'total_bytes': manifest['total_bytes']}))


if __name__ == '__main__':
    main()

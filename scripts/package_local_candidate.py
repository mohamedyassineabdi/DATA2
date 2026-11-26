"""Package the ignored candidate copy for later authorized encryption/transfer.

The ZIP is not encrypted. Never upload it or treat it as redistribution approval.
"""
import hashlib
import json
import zipfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
local = root / 'local_only'
output = local / 'transfer_pending' / 'DATA2_local_candidate_v2.zip'
if not (local / 'audit/canonical_mapping.jsonl').is_file() or not (local / 'data').is_dir():
    raise SystemExit('Protected local candidate copy is absent; refusing to create an empty archive')
if output.exists():
    raise SystemExit('Archive already exists; refusing to overwrite it')
output.parent.mkdir(parents=True, exist_ok=True)
paths = [p for base in (local / 'data', local / 'audit') for p in base.rglob('*') if p.is_file()]
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
    for path in sorted(paths):
        archive.write(path, path.relative_to(local).as_posix())
with zipfile.ZipFile(output) as archive:
    failure = archive.testzip()
    if failure or len(archive.namelist()) != len(paths):
        output.unlink()
        raise RuntimeError('ZIP integrity check failed')
digest = hashlib.sha256()
with output.open('rb') as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
result = {'archive': output.relative_to(root).as_posix(), 'bytes': output.stat().st_size,
          'sha256': digest.hexdigest(), 'files': len(paths), 'encrypted': False,
          'status': 'LOCAL_ONLY_NO_EXTERNAL_TRANSFER'}
(output.parent / 'archive_manifest.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result))

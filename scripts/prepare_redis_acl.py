"""Create an ignored Redis ACL file for the optional coordination profile."""
import getpass
import hashlib
import os
from pathlib import Path


root = Path(__file__).resolve().parents[1]
target = root / 'infrastructure/redis-users.local.acl'
if target.exists():
    raise SystemExit('ACL file already exists; refusing to overwrite it')
password = os.environ.get('REDIS_COORDINATION_PASSWORD') or getpass.getpass('Redis coordination password: ')
if len(password) < 20 or password.startswith('replace-with-'):
    raise SystemExit('Use a unique password of at least 20 characters')
password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
target.write_bytes(f'user default off\nuser dalila on #{password_hash} ~* +@read +@write +ping\n'.encode('ascii'))
try:
    target.chmod(0o600)
except OSError:
    pass
print('Created local Redis ACL file; its password was not displayed')

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from write_public_manifest import is_public_file


class PublicManifestTests(unittest.TestCase):
    def test_private_configuration_is_excluded(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            infra = root / 'infrastructure'
            infra.mkdir()
            env = infra / '.env'
            env.write_text('secret=placeholder')
            template = infra / 'env.example'
            template.write_text('secret=replace-me')
            self.assertFalse(is_public_file(env))
            self.assertTrue(is_public_file(template))


if __name__ == '__main__':
    unittest.main()

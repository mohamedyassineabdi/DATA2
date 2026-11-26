"""Test installation boundaries without reading any protected source records."""
import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path


SPEC = importlib.util.spec_from_file_location('setup_data', Path(__file__).resolve().parents[1] / 'scripts/setup_data.py')
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)


class SetupDataTests(unittest.TestCase):
    def test_public_manifest_is_self_consistent(self):
        self.assertGreater(SETUP.verify_public(), 0)

    def test_archive_requires_strong_expected_hash(self):
        with self.assertRaisesRegex(RuntimeError, 'requires --archive-sha256'):
            SETUP.archive_expected_hash(Path('other.zip'), None)
        with self.assertRaisesRegex(RuntimeError, '64 hexadecimal'):
            SETUP.archive_expected_hash(Path('other.zip'), 'wrong')

    def test_rejects_unsafe_archive_members(self):
        for name in ('../outside', '/absolute', 'data/../outside', 'data//evil'):
            with self.subTest(name=name):
                stream = io.BytesIO()
                with zipfile.ZipFile(stream, 'w') as archive:
                    archive.writestr(name, b'fixture')
                    archive.writestr('audit/canonical_mapping.jsonl', b'')
                    archive.writestr('audit/dataset_manifest.json', b'{}')
                stream.seek(0)
                with zipfile.ZipFile(stream) as archive:
                    with self.assertRaisesRegex(RuntimeError, 'unsafe'):
                        SETUP.safe_members(archive)

    def test_archive_is_checked_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'other.zip'
            archive.write_bytes(b'not a ZIP')
            with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
                SETUP.install_archive(archive, '0' * 64)


if __name__ == '__main__':
    unittest.main()

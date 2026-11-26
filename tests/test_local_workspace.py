import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_local_workspace import row_count, sha256


class LocalWorkspaceTests(unittest.TestCase):
    def test_row_counts_include_final_line_without_newline(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            jsonl = folder / 'rows.jsonl'
            jsonl.write_text('{"a":1}\n{"a":2}', encoding='utf-8')
            csv = folder / 'rows.csv'
            csv.write_text('a\n1\n2', encoding='utf-8')
            self.assertEqual(row_count(jsonl), 2)
            self.assertEqual(row_count(csv), 2)

    def test_hash_uses_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'x.bin'
            path.write_bytes(b'abc')
            self.assertEqual(sha256(path), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')


if __name__ == '__main__':
    unittest.main()

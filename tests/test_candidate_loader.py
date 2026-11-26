import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from load_candidate_stack import load_env, sparse_vector


class CandidateLoaderTests(unittest.TestCase):
    def test_sparse_vector_is_stable_and_language_agnostic(self):
        first = sparse_vector('zone منطقة zone')
        second = sparse_vector('ZONE منطقة zone')
        self.assertEqual(first, second)
        self.assertEqual(sum(first['values']), 3.0)
        self.assertEqual(first['indices'], sorted(first['indices']))

    def test_env_file_parser_keeps_secrets_out_of_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text('# local\nTEST_PASSWORD=example-only\n', encoding='utf-8')
            self.assertEqual(load_env(path)['TEST_PASSWORD'], 'example-only')


if __name__ == '__main__':
    unittest.main()

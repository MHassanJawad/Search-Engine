import json
import tempfile
import unittest
from pathlib import Path

from search_engine import SearchEngine
from text_processing import singular_candidate, tokenize


class TextProcessingTests(unittest.TestCase):
    def test_tokenization_and_plural_normalization(self):
        self.assertEqual(tokenize("Climate-change's 2024 impact"), ["climate", "change's", "2024", "impact"])
        self.assertEqual(singular_candidate("changes"), "change")
        self.assertEqual(singular_candidate("news"), "news")


class SearchEngineTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        data_dir = Path(self.temporary_directory.name)
        fixtures = {
            "doc_metadata.json": {
                "1": {"title": "Climate report", "description": "First", "url": "https://one", "url_to_image": ""},
                "2": {"title": "Policy", "description": "Second", "url": "https://two", "url_to_image": ""},
            },
            "doc_lengths.json": {"1": 100, "2": "200"},
            "barrel_c.json": {"climate": {"1": "3", "2": 1}, "change": {"2": "4"}},
        }
        for filename, value in fixtures.items():
            (data_dir / filename).write_text(json.dumps(value), encoding="utf-8")
        self.engine = SearchEngine(data_dir)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_search_accepts_legacy_string_numbers(self):
        results = self.engine.search("climate")
        self.assertEqual([result["doc_id"] for result in results], ["1", "2"])

    def test_plural_query_uses_singular_index_term(self):
        self.assertEqual(self.engine.search("changes")[0]["doc_id"], "2")

    def test_empty_query_has_no_results(self):
        self.assertEqual(self.engine.search("  "), [])


if __name__ == "__main__":
    unittest.main()

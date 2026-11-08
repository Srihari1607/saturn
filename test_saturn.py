import base64
import csv
import io
import re
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app import app
from models import ROOT, REVISION
from saturn import analyze, export_csv, read_records, summarize

DEMO = Path(__file__).parent / "examples" / "demo.csv"


class WorkflowTests(unittest.TestCase):
    def test_csv_validation(self):
        for text in ("", "other\na\n", "text,text\na,b\n", "text\na,b\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                list(read_records(io.StringIO(text)))
        self.assertEqual(list(read_records(io.StringIO("Review\n"))), [])
        self.assertEqual(summarize([], ["vader"])["vader"]["net_sentiment"], None)

    def test_single_class_and_tie(self):
        for comments, expected in [(["I love it"], 100), (["I love it", "Awful"], 0)]:
            records = read_records(io.StringIO("Review\n" + "\n".join(comments)))
            rows = analyze(records, ["vader"])
            self.assertEqual(summarize(rows, ["vader"])["vader"]["net_sentiment"], expected)

    def test_separate_submissions(self):
        def submit(word):
            with app.test_client() as client:
                response = client.post("/", data={"text": word})
                self.assertEqual(response.status_code, 200)
                return response.get_data(as_text=True)
        with ThreadPoolExecutor(2) as pool:
            first, second = pool.map(submit, ["UniqueAlpha", "UniqueBeta"])
        self.assertNotIn("UniqueBeta", first)
        self.assertNotIn("UniqueAlpha", second)

    def test_invalid_upload(self):
        with app.test_client() as client:
            response = client.post("/", data={"file": (io.BytesIO(b"wrong\n1"), "bad.csv")})
            self.assertEqual(response.status_code, 400)

    @unittest.skipUnless((ROOT / REVISION / "pytorch_model.bin").exists(), "install RoBERTa for paired inference")
    def test_paired_web_export_matches_batch(self):
        names = ["vader", "roberta"]
        with DEMO.open(encoding="utf-8", newline="") as stream:
            expected = analyze(read_records(stream), names)
        self.assertEqual(len(expected), 10)
        for name, summary in summarize(expected, names).items():
            self.assertEqual((summary["scored"], summary["skipped"]), (4, 1), name)
        with app.test_client() as client:
            response = client.post("/", data={"model": "both", "file": (io.BytesIO(DEMO.read_bytes()), "demo.csv")})
        self.assertEqual(response.status_code, 200)
        match = re.search(rb'data:text/csv;base64,([^"]+)', response.data)
        self.assertEqual(base64.b64decode(match[1]).decode(), export_csv(expected))

    @unittest.skipUnless((ROOT / REVISION / "pytorch_model.bin").exists(), "install RoBERTa for length checks")
    def test_long_unicode_input(self):
        text = "Great café 😊 " * 240
        row, = analyze([{"text": text}], ["roberta"])
        self.assertEqual(row["text"], text)
        self.assertTrue(row["truncated"])
        self.assertAlmostEqual(sum(row[k] for k in ("p_negative", "p_neutral", "p_positive")), 1, places=5)


if __name__ == "__main__":
    unittest.main()

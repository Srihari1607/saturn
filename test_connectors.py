import base64
import io
import json
import re
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import app
from connectors import amazon, collect, index_amazon, parse_url, timestamp, unique_records, youtube
from preprocessing import preprocess
from saturn import analyze, daily_trends, read_records


class ConnectorTests(unittest.TestCase):
    def test_youtube_applies_limit_to_extractor(self):
        with patch("yt_dlp.YoutubeDL") as downloader:
            downloader.return_value.__enter__.return_value.extract_info.return_value = {"comments": []}
            youtube("jNQXAC9IVRw", 5)
            args = downloader.call_args.args[0]["extractor_args"]["youtube"]["max_comments"]
            self.assertEqual(args, ["5", "5", "0", "0", "1"])

    def test_url_validation(self):
        self.assertEqual(parse_url("https://youtu.be/dQw4w9WgXcQ?t=2"), ("youtube", "dQw4w9WgXcQ"))
        self.assertEqual(parse_url("https://www.amazon.in/item/dp/B0742LVLMJ/ref=abc"), ("amazon", "B0742LVLMJ"))
        self.assertEqual(parse_url("https://www.instagram.com/reel/Ab_123/"), ("instagram", "Ab_123"))
        for url in ["http://youtube.com/watch?v=dQw4w9WgXcQ", "https://youtube.com.evil.org/watch?v=dQw4w9WgXcQ",
                    "https://localhost", "https://user@youtube.com/watch?v=dQw4w9WgXcQ",
                    "https://youtube.com:443/watch?v=dQw4w9WgXcQ", "https://youtu.be/a/b"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_url(url)

    def test_amazon_index_and_failed_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            source, database = Path(directory) / "fixture.jsonl", Path(directory) / "reviews.sqlite"
            source.write_text(json.dumps({"asin": "B0742LVLMJ", "parent_asin": "B012345678",
                                         "text": "Excellent", "timestamp": 1609459200000}) + "\n", encoding="utf-8")
            index_amazon(source, database)
            result = amazon("B0742LVLMJ", 100, database)
            self.assertEqual(result["records"][0]["timestamp"], "2021-01-01T00:00:00+00:00")
            self.assertEqual(amazon("B012345678", 100, database)["records"], [])
            source.write_text("invalid", encoding="utf-8")
            with self.assertRaises(ValueError):
                index_amazon(source, database)
            self.assertEqual(amazon("B0742LVLMJ", 100, database)["records"], result["records"])

    def test_timezone_duplicates_and_cap(self):
        self.assertEqual(timestamp("2025-01-02T00:30:00+05:30"), "2025-01-01T19:00:00+00:00")
        comments = [{"id": 1, "text": "Good"}, {"id": 1, "text": "Good"}, {"id": 2, "text": "Bad"}]
        self.assertEqual(len(unique_records(comments, "youtube", "post", 100)), 2)
        self.assertEqual(len(unique_records(comments, "youtube", "post", 1)), 1)

    def test_profiles_and_trends(self):
        text = "I am NOT happy @shop https://example.com #service 😠"
        self.assertEqual(preprocess(text, "raw-v1"), text)
        self.assertIn("NOT", preprocess(text, "social-v1"))
        self.assertNotIn("https://", preprocess(text, "paper-v1"))
        rows = analyze(read_records(io.StringIO("text,timestamp\nGreat!,2025-01-02T00:30:00+05:30\nAwful,\n")),
                       ["vader"])
        trend, missing = daily_trends(rows)
        self.assertEqual((trend[0]["date"], trend[0]["net_sentiment"], missing), ("2025-01-01", 100, 1))

    def test_timeout_and_collection_error_reach_form(self):
        # Exercise our process boundary without depending on platform availability.
        with patch("connectors.subprocess.run", side_effect=subprocess.TimeoutExpired("collector", 90)):
            with app.test_client() as client:
                response = client.post("/", data={"url": "https://youtu.be/dQw4w9WgXcQ"})
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"timed out", response.data)
        self.assertNotIn(b"Download predictions", response.data)

    def test_fixture_collection_export(self):
        result = {"records": [{"record_id": "comment-1", "source": "youtube", "post_id": "video",
                               "timestamp": "2025-01-01", "text": "Excellent!"}],
                  "title": "Example video", "details": "YouTube fixture", "warnings": ["Partial collection"], "limited": True,
                  "retrieved_at": "2026-11-08"}
        with patch("app.collect", return_value=result), app.test_client() as client:
            response = client.post("/", data={"url": "https://youtu.be/dQw4w9WgXcQ"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Daily sentiment", response.data)
        self.assertLess(response.data.index(b"Example video"), response.data.index(b"Overall comment summary"))
        self.assertLess(response.data.index(b"Overall comment summary"), response.data.index(b"Overall sentiment score"))
        self.assertIn(b"The collected comments are mostly positive.", response.data)
        payload = re.search(rb"data:text/csv;base64,([^\"]+)", response.data)[1]
        self.assertIn("comment-1", base64.b64decode(payload).decode())

    def test_form_input_conflicts_and_bad_encoding(self):
        with app.test_client() as client:
            response = client.post("/", data={"url": "https://youtu.be/dQw4w9WgXcQ", "text": "Great"})
            self.assertEqual(response.status_code, 400)
            response = client.post("/", data={"file": (io.BytesIO(b"Comment\n\xff"), "bad.csv")})
            self.assertEqual(response.status_code, 400)
            response = client.post("/", data={"text": "Good", "preprocessing": "unknown"})
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()

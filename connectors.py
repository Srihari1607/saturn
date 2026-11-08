"""Bounded comment collection and indexed historical Amazon review lookup."""
import argparse
import gzip
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

RESOURCE_DIR = Path(__file__).resolve().parent / ".resources"
DATABASE = RESOURCE_DIR / "amazon.sqlite"


def parse_url(url):
    parsed = urlsplit(url.strip())
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
        raise ValueError("Use an HTTPS link without credentials or a custom port.")
    host = (parsed.hostname or "").lower()
    path = parsed.path.rstrip("/")
    if host in ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"):
        if host == "youtu.be":
            identifier = path.lstrip("/")
        elif path == "/watch":
            identifier = parse_qs(parsed.query).get("v", [""])[0]
        else:
            match = re.fullmatch(r"/(?:shorts|embed)/([\w-]{11})", path)
            identifier = match[1] if match else ""
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", identifier):
            return "youtube", identifier
    elif host in ("instagram.com", "www.instagram.com"):
        match = re.fullmatch(r"/(?:p|reel)/([A-Za-z0-9_-]+)", path)
        if match:
            return "instagram", match[1]
    elif host in ("amazon.com", "www.amazon.com", "amazon.in", "www.amazon.in",
                  "amazon.co.uk", "www.amazon.co.uk"):
        match = re.search(r"/(?:dp|gp/product|product-reviews)/([A-Z0-9]{10})(?:/|$)", path)
        if match:
            return "amazon", match[1]
    raise ValueError("Use a YouTube video, Instagram post/Reel, or Amazon product link.")


def timestamp(value):
    if value is None or value == "":
        return ""
    try:
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 10**11 else value
            return datetime.fromtimestamp(seconds, timezone.utc).isoformat()
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return ""


def unique_records(comments, source, post_id, limit):
    seen = set()
    records = []
    for comment in comments:
        identifier = str(comment["id"])
        if identifier in seen:
            continue
        seen.add(identifier)
        records.append({"record_id": identifier, "source": source, "post_id": post_id,
                        "timestamp": timestamp(comment.get("timestamp")), "text": comment.get("text") or ""})
        if len(records) == limit:
            break
    return records


def youtube(identifier, limit):
    import yt_dlp
    warnings = []

    class Logger:
        def debug(self, message):
            pass

        def warning(self, message):
            warnings.append(str(message))

        def error(self, message):
            pass

    options = {"skip_download": True, "getcomments": True, "noplaylist": True,
               "quiet": True, "socket_timeout": 15, "retries": 1, "extractor_retries": 1,
               "ignore_no_formats_error": True, "logger": Logger(),
               "js_runtimes": {"node": {}},
               "extractor_args": {"youtube": {"max_comments": [str(limit), str(limit), "0", "0", "1"],
                                              "comment_sort": ["new"]}}}
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(f"https://www.youtube.com/watch?v={identifier}", download=False)
    comments = [row for row in info.get("comments", []) if row.get("parent", "root") == "root"]
    records = unique_records(comments, "youtube", identifier, limit)
    return {"records": records, "details": "YouTube · newest top-level comments",
            "title": info.get("title") or "YouTube video",
            "warnings": warnings, "limited": len(records) >= limit}


def instagram(identifier, limit):
    import instaloader
    loader = instaloader.Instaloader(quiet=True, max_connection_attempts=1, request_timeout=15)
    username = os.environ.get("SATURN_INSTAGRAM_USER")
    session = os.environ.get("SATURN_INSTAGRAM_SESSION")
    if username and session:
        loader.load_session_from_file(username, session)
    post = instaloader.Post.from_shortcode(loader.context, identifier)
    records = []
    warnings = []
    try:
        for comment in post.get_comments():
            records.append({"id": comment.id, "text": comment.text,
                            "timestamp": comment.created_at_utc.isoformat()})
            if len(records) >= limit:
                break
    except instaloader.exceptions.InstaloaderException as error:
        if not records:
            raise RuntimeError("Instagram comments unavailable. Configure a local Instaloader session or upload a CSV.") from error
        warnings.append("Instagram stopped returning comments; these results cover the retrieved subset.")
    return {"records": unique_records(records, "instagram", identifier, limit),
            "details": "Instagram · top-level comments", "warnings": warnings, "limited": len(records) >= limit}


def index_amazon(source, database=DATABASE):
    """Replace the index atomically so failed imports preserve the previous dataset."""
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=database.parent, suffix=".sqlite")
    os.close(handle)
    with Path(source).open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    opener = gzip.open if str(source).endswith(".gz") else open
    try:
        with closing(sqlite3.connect(temporary)) as connection, connection:
            connection.execute("CREATE TABLE reviews (id TEXT PRIMARY KEY, asin TEXT, parent TEXT, text TEXT, timestamp TEXT)")
            with opener(source, "rt", encoding="utf-8") as stream:
                for number, line in enumerate(stream, 1):
                    item = json.loads(line)
                    connection.execute("INSERT INTO reviews VALUES (?,?,?,?,?)",
                                       (str(number), item["asin"], item.get("parent_asin", ""),
                                        item.get("text") or "", timestamp(item.get("timestamp"))))
            connection.execute("CREATE INDEX review_asin ON reviews(asin)")
            connection.execute("CREATE TABLE metadata (filename TEXT, sha256 TEXT)")
            connection.execute("INSERT INTO metadata VALUES (?,?)", (Path(source).name, checksum))
        os.replace(temporary, database)
    finally:
        Path(temporary).unlink(missing_ok=True)


def amazon(identifier, limit, database=DATABASE):
    if not Path(database).is_file():
        raise RuntimeError("Amazon dataset is missing. Import a review JSONL using connectors.py index-amazon, or upload a CSV.")
    with closing(sqlite3.connect(f"{Path(database).resolve().as_uri()}?mode=ro", uri=True)) as connection:
        rows = connection.execute("SELECT id,text,timestamp FROM reviews WHERE asin=? ORDER BY timestamp DESC,id LIMIT ?",
                                  (identifier, limit + 1)).fetchall()
        filename, checksum = connection.execute("SELECT filename,sha256 FROM metadata").fetchone()
    records = unique_records(({"id": row[0], "text": row[1], "timestamp": row[2]} for row in rows),
                             "amazon-historical", identifier, limit)
    return {"records": records, "details": f"Historical Amazon reviews · exact ASIN · {filename}",
            "dataset_sha256": checksum, "warnings": [], "limited": len(rows) > limit}


def collect(url, limit=100):
    if not 1 <= limit <= 100:
        raise ValueError("Choose between 1 and 100 comments.")
    source, identifier = parse_url(url)
    if source == "amazon":
        result = amazon(identifier, limit)
    else:
        try:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "fetch", source,
                                      identifier, str(limit)], capture_output=True, encoding="utf-8",
                                     timeout=90, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Collection timed out after 90 seconds. Try again or upload a CSV.") from error
        if process.returncode:
            raise RuntimeError(f"{source.title()} could not retrieve comments. {process.stderr.strip()[-700:]} Upload a CSV to continue.")
        result = json.loads(process.stdout)
    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    if not result["records"]:
        result["warnings"].append("No matching reviews in the loaded dataset." if source == "amazon"
                                  else "No comments were returned. Comments may be disabled or inaccessible.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index-amazon")
    index.add_argument("path", type=Path)
    fetch = commands.add_parser("fetch")
    fetch.add_argument("source", choices=["youtube", "instagram"])
    fetch.add_argument("identifier")
    fetch.add_argument("limit", type=int)
    args = parser.parse_args()
    try:
        if args.command == "index-amazon":
            index_amazon(args.path)
            print(f"Imported {args.path.name}")
        else:
            function = youtube if args.source == "youtube" else instagram
            print(json.dumps(function(args.identifier, args.limit)))
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

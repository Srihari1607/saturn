"""Run SATURN on an Instagram-style Comment CSV or an Amazon-style Review CSV."""
import argparse
import csv
import io
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

from models import LABELS, REVISION, scorer
from preprocessing import preprocess, PROFILES

FIELDS = ("record_id", "source", "post_id", "timestamp", "text", "model", "version",
          "status", "reason", "label", "compound", "p_negative", "p_neutral", "p_positive", "truncated",
          "preprocessing", "processed_text")


def read_records(stream):
    reader = csv.DictReader(stream, strict=True)
    headers = reader.fieldnames or []
    if len(headers) != len(set(headers)):
        raise ValueError("Duplicate CSV column names.")
    column = next((key for key in ("text", "Comment", "Review") if key in headers), None)
    if column is None:
        raise ValueError("Include a text, Comment, or Review column.")
    for number, row in enumerate(reader, start=1):
        if None in row:
            raise ValueError(f"Extra CSV fields in record {number}.")
        yield {"record_id": row.get("record_id") or row.get("id") or str(number),
               "source": row.get("source", ""), "post_id": row.get("post_id") or row.get("product_id", ""),
               "timestamp": row.get("timestamp", ""), "text": row[column] or ""}


def analyze(records, names, profile="raw-v1"):
    if not names or any(name not in ("vader", "roberta") for name in names):
        raise ValueError("Choose VADER or RoBERTa.")
    predictions = []
    for record in records:
        processed = preprocess(record["text"], profile)
        for name in names:
            row = {**record, "model": name, "version": REVISION if name == "roberta" else "nltk-3.9.2",
                   "preprocessing": profile, "processed_text": processed}
            if processed.strip():
                row.update(status="scored", **scorer(name)(processed))
            else:
                row.update(status="skipped", reason="blank text" if not record["text"].strip() else "empty after preprocessing")
            predictions.append(row)
    return predictions


def summarize(rows, names):
    summaries = {}
    for name in names:
        subset = [row for row in rows if row["model"] == name]
        counts = Counter(row["label"] for row in subset if row["status"] == "scored")
        total = counts.total()
        summaries[name] = {"scored": total, "skipped": len(subset) - total,
                           "counts": {label: counts[label] for label in LABELS},
                           "net_sentiment": 100 * (counts["Positive"] - counts["Negative"]) / total if total else None}
    return summaries


def daily_trends(rows):
    groups = {}
    missing = 0
    for row in rows:
        if row["status"] != "scored":
            continue
        try:
            moment = datetime.fromisoformat((row.get("timestamp") or "").replace("Z", "+00:00"))
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=timezone.utc)
            day = moment.astimezone(timezone.utc).date().isoformat()
        except ValueError:
            missing += 1
            continue
        key = (day, row["model"])
        groups.setdefault(key, []).append(row)
    return [{"date": day, "model": model, **summarize(group, [model])[model]}
            for (day, model), group in sorted(groups.items())], missing


def export_csv(rows):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", choices=["vader", "roberta", "both"], default="vader")
    parser.add_argument("--preprocessing", choices=PROFILES, default="raw-v1")
    args = parser.parse_args()
    names = ["vader", "roberta"] if args.model == "both" else [args.model]
    if args.input.resolve() == args.output.resolve():
        parser.error("Choose a separate output path.")
    try:
        with args.input.open(encoding="utf-8-sig", newline="") as stream:
            rows = analyze(read_records(stream), names, args.preprocessing)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as temp:
            temp.write(export_csv(rows).encode("utf-8"))
        try:
            os.replace(temp.name, args.output)
        finally:
            Path(temp.name).unlink(missing_ok=True)
    except (OSError, ValueError, csv.Error, RuntimeError, ImportError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(summarize(rows, names), indent=2))


if __name__ == "__main__":
    main()

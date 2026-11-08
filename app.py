"""Local SATURN review workspace. Each response contains only its submitted rows."""
import base64
import csv
import io
from pathlib import Path

from flask import Flask, render_template, request, send_file

from saturn import analyze, export_csv, read_records, summarize, daily_trends
from connectors import collect

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(ROOT), static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


@app.get("/style.css")
def stylesheet():
    return send_file(ROOT / "style.css")


@app.route("/", methods=["GET", "POST"])
def home():
    context = {"selected": "vader"}
    if request.method == "GET":
        return render_template("index.html", **context)
    selected = request.form.get("model", "vader")
    if selected not in ("vader", "roberta", "both"):
        return render_template("index.html", error="Choose a listed model.", **context), 400
    names = ["vader", "roberta"] if selected == "both" else [selected]
    context["selected"] = selected
    try:
        upload = request.files.get("file")
        text = request.form.get("text", "")
        url = request.form.get("url", "").strip()
        if sum([bool(upload), bool(text.strip()), bool(url)]) != 1:
            raise ValueError("Submit one input: text, a CSV, or a supported URL.")
        if url:
            collection = collect(url)
            records = collection["records"]
            context["collection"] = collection
        elif upload:
            records = list(read_records(io.StringIO(upload.read().decode("utf-8-sig"), newline="")))
        elif text.strip():
            records = [{"text": text, "record_id": "1", "source": "pasted text",
                        "timestamp": "", "post_id": ""}]
        else:
            raise ValueError("Enter some text or choose a CSV.")
        if len(records) > 1000:
            raise ValueError("Use the command line for files with more than 1,000 rows.")
        rows = analyze(records, names, request.form.get("preprocessing", "raw-v1"))
    except (ValueError, csv.Error) as error:
        return render_template("index.html", error=str(error), **context), 400
    except (RuntimeError, ImportError, OSError) as error:
        return render_template("index.html", error=str(error), **context), 503
    payload = base64.b64encode(export_csv(rows).encode("utf-8")).decode("ascii")
    trends, missing_dates = daily_trends(rows)
    summaries = summarize(rows, names)
    for summary in summaries.values():
        counts = summary["counts"]
        if not summary["scored"]:
            summary["overview"] = "No comments could be scored."
        else:
            largest = max(counts.values())
            leaders = [label.lower() for label, count in counts.items() if count == largest]
            tone = "mixed" if len(leaders) > 1 else f"mostly {leaders[0]}"
            summary["overview"] = (
                f"The collected comments are {tone}. Of {summary['scored']} scored comments, "
                f"{counts['Positive']} are positive, {counts['Neutral']} neutral and "
                f"{counts['Negative']} negative."
            )
    return render_template("index.html", rows=rows[:20], total=len(rows), payload=payload,
                           summaries=summaries, trends=trends[-30:], trend_count=len(trends),
                           missing_dates=missing_dates, **context)


@app.errorhandler(413)
def too_large(error):
    return render_template("index.html", selected="vader", error="Upload a CSV smaller than 2 MiB."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050)

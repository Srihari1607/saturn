# SATURN
Sentiment analysis for comments and product reviews. Compare the paper's NLTK VADER baseline with the pinned English Cardiff NLP RoBERTa checkpoint on the same records. Use the local web form for pasted text or a CSV, or use the CLI for repeatable batch analysis.

YouTube results begin with the video title, an overall summary of the collected comments and a signed sentiment score. Class distributions, daily trends and individual predictions follow. The summary describes the model's classification counts. Collection warnings and retrieval details are available in an expandable section.

## Run on Windows
From the repository directory, with Python 3.12 and PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe models.py vader
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5050. Enter one input per submission, either a URL, pasted text or CSV. For the optional transformer comparison, stop the server, run the following commands, and start it again:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-roberta.txt
.\.venv\Scripts\python.exe models.py roberta
```

Setup requires internet access. Inference reads the cached resources from `.resources/`. The RoBERTa weights require roughly 500 MB in addition to the Python dependencies. VADER setup verifies the lexicon archive's SHA-256. Original text is the default. The text preparation selector also offers social normalization and a lowercased variant with a small explicit stop list that retains negation. Every export includes original and processed text and the profile version. RoBERTa truncates at 512 tokens including boundary tokens and flags affected records.

## URL inputs

- YouTube accepts watch, short and youtu.be links. It collects up to 100 newest top-level comments with yt-dlp, scores them and exports the results. Collection has a 90-second timeout. Node.js on PATH is used when available. Upstream restrictions may require a retry or CSV input. A live test of `https://www.youtube.com/watch?v=jNQXAC9IVRw` retrieved and scored 100 comments on 8 November 2026.
- Amazon accepts product links on amazon.com, amazon.in and amazon.co.uk and looks up the exact ASIN in the loaded historical dataset. The local installation contains 16,216 reviews from UCSD's Subscription Boxes category. Try `https://www.amazon.com/dp/B0742LVLMJ`. Product availability in the dataset determines coverage. Date ranges come from historical review timestamps. An absent product returns a coverage message.
- Instagram accepts post and Reel links through Instaloader. Live collection remains unverified. When login is required, create an Instaloader session locally and set `SATURN_INSTAGRAM_USER` and `SATURN_INSTAGRAM_SESSION` before starting the app. Keep the session file under the ignored `.resources/` directory or another private local directory.

To load or replace the Amazon subset:

```powershell
curl.exe -fL https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/Subscription_Boxes.jsonl.gz -o .resources/Subscription_Boxes.jsonl.gz
.\.venv\Scripts\python.exe connectors.py index-amazon .resources/Subscription_Boxes.jsonl.gz
```

The importer also accepts uncompressed JSONL with `asin`, `text`, optional `parent_asin` and millisecond `timestamp` fields. Imports replace the index atomically. The original CSV upload workflow remains available for other reviews.

## Batch and verification
```powershell
.\.venv\Scripts\python.exe saturn.py examples/demo.csv results/predictions.csv --model both
.\.venv\Scripts\python.exe -m unittest discover -v
```

Use `--model vader` for the lightweight setup. Transformer tests run when the checkpoint is installed. The synthetic fixture contains five rows including one blank. It demonstrates processing and supplies no human reference labels.

CSV inputs use UTF-8 (optional BOM). Text column preference is `text`, `Comment`, then `Review`. Optional fields are `record_id` or `id`, `source`, `post_id` or `product_id`, and `timestamp`. Other columns stay in the source CSV. Each model emits one output row per input row. CSV duplicates retain their original frequency; connectors deduplicate by comment ID. Blank text and text emptied by preprocessing are recorded as skipped. The local web interface accepts up to 1,000 rows and a 2 MiB request. Downloads include every prediction and full text; the preview displays 20 abbreviated records.

Daily trends use UTC dates and show up to 30 recent day/model totals. Predictions without valid dates are excluded with a displayed count. Naive timestamps are interpreted as UTC.

For browser checks, install `requirements-test.txt` and Google Chrome, then run `python check_browser.py`. This starts and stops its own local server and tests live YouTube retrieval, historical Amazon lookup, CSV export and mobile layout. `python check_live.py` separately records live collection outcomes. Both save evidence under `results/`.

VADER uses the compound polarity score with inclusive thresholds of ±0.05. RoBERTa returns three probabilities and the most likely label. Net sentiment is 100 × (positive count − negative count) / scored count. Accuracy requires separate human labels.

## Research status
The historical notebook retains its recorded output. The original 1,000-comment file and screenshot application still need recovery. YouTube retrieval, historical Amazon lookup and daily trends are implemented. Instagram live acceptance, human-labeled accuracy studies, preprocessing comparisons and the paper's timing experiments remain open. Current comparison covers VADER and RoBERTa. See [implementation plan](plan.md) and [test results](TEST_RESULTS.md). The local server is for development.

[Cardiff NLP checkpoint](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment/tree/daefdd1f6ae931839bce4d0f3db0a1a4265cd50f) · [NLTK data collection](https://github.com/nltk/nltk_data)

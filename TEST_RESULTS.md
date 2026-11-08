# SATURN application test results

Tested on 8 November 2026. Application functions and data collection are the scope of this record.

| Check | Observed result |
|---|---|
| Regression suite | 14 tests passed, including real VADER/RoBERTa scoring, repeat inference/export equality, empty and invalid input, long Unicode input, timezone handling and request isolation. |
| YouTube browser workflow | Pasted the public video URL ending in jNQXAC9IVRw, retrieved 100 comments, scored them with VADER and downloaded their predictions. |
| YouTube limit regression | Corrected the extractor argument to a list of five values. A single comma-joined value previously allowed retrieval beyond the cap and caused a timeout. |
| Amazon browser workflow | Pasted a product link for B0742LVLMJ and scored 100 historical reviews from the loaded UCSD Subscription Boxes category. |
| Absent Amazon product | B000000000 returned a dataset coverage message and zero scored records. |
| Browser upload/export | Uploaded the five-row demo, checked daily totals and downloaded predictions. |
| Responsive page | Chrome at a 390-pixel viewport reported no horizontal page overflow. Screenshot inspected. |
| Input errors | Unsupported URLs, multiple input types, invalid UTF-8/CSV and unknown preprocessing profiles produced errors. |
| Interrupted collection | Injected process timeout reached the form as a visible error without a sentiment result. |
| Amazon import failure | Invalid replacement JSONL preserved the previous database and its records. |
| Fresh base setup | Installed requirements.txt in an isolated environment and scored the five-row demo. Four scored, one skipped, net sentiment +25. |

## Commands

Run from the repository directory after setup.

```powershell
./.venv/Scripts/python.exe -m unittest discover -v
./.venv/Scripts/python.exe check_browser.py
./.venv/Scripts/python.exe check_live.py
./.venv/Scripts/python.exe saturn.py examples/demo.csv results/predictions.csv --model both
```

Browser checks require requirements-test.txt and an installed Google Chrome. They start a temporary local server and shut it down on completion. Live tests depend on platform availability.

## Saved local evidence

- `results/browser-checks.json` records seven passed browser checks.
- `results/live-checks.json` records the final five-comment YouTube probe, Amazon match and Amazon miss.
- `results/youtube-predictions.csv` contains the 100 live comments and scores exported by the browser.
- `results/browser-predictions.csv` contains the uploaded fixture's browser export.
- `results/amazon-desktop.png`, `amazon-mobile.png` and `youtube-mobile.png` capture the rendered pages.
- `results/build-manifest.json` records runtime versions and source/data hashes.
- `results/clean-vader.csv` records the fresh base-environment run.

These files are local test outputs in the ignored results directory. The full Amazon index and downloaded resources also stay local under .resources.

## Remaining limits

Instagram collection is implemented but a probe failed during post metadata retrieval. A known accessible post and a working local session are still needed for successful live acceptance. The failed probe used an unverified example shortcode, so it establishes error handling only.

YouTube returned video-format JavaScript challenge warnings while successfully returning comments. The recorded success covers the tested public video and date. Other videos may return access errors or require a retry.

Amazon uses 16,216 historical reviews in the Subscription Boxes category. A product outside that subset needs another category imported or a CSV upload.

The model suite ran using the existing local transformer environment. Fresh-install validation covered the base VADER environment. Original-paper reproduction, human annotation, statistical accuracy comparison and 1,000-comment timing experiments remain deferred. These application tests do not close those plan items.

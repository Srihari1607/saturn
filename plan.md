# SATURN implementation and verification plan

Track progress against the [roadmap](ROADMAP.md). The reference is *Sentiment Analysis Tool and User Review on Network (SATURN)*, ICAIH-2025 paper 196. Figure numbers refer to the manuscript inside the supplied PDF.

### First build · 6 November 2026

- [x] Replace the broken batch entry point and score the synthetic fixture with pinned NLTK VADER and Cardiff NLP RoBERTa resources. Both models scored four records and skipped one blank. The CLI saves the predictions and prints separate summaries per model.
- [x] Connect direct text, Instagram-style and Amazon-style CSV input to the same scoring functions. Add class distribution, signed net sentiment, per-record scores and a full CSV export to the local web application.
- [x] Run six workflow regression tests, including an exact comparison of the web export with a second inference run, long Unicode input, invalid uploads, and concurrent text submissions. Submit a real HTTP request and verify the returned VADER score.
### Application build and tests · 8 November 2026

- [x] Implement YouTube retrieval with yt-dlp and test the full browser workflow on 100 real comments.
- [x] Index 16,216 historical Amazon reviews and test a covered product, an absent product and CSV export.
- [x] Implement Instagram collection with optional local Instaloader session configuration. Live acceptance remains open below.
- [x] Add versioned preprocessing, full-text exports, UTC daily trends, collection limits, status messages and explicit empty/error states.
- [x] Pass 14 automated tests and seven real-browser checks, including mobile layout, real model scoring and YouTube retrieval.
- [x] Install the base requirements into a fresh isolated environment and run the VADER sample successfully.

**Remaining application acceptance.** Instagram needs a known accessible post and, when required, a working local session. The live probe returned a metadata/access failure. The app reports this and offers CSV upload.

**Research work is deferred** following the user's request to focus on completing the application. M0, M3 and the manuscript experiments in M4 retain their open tasks. See [test results](TEST_RESULTS.md) for commands, observed results and evidence files.

## M0 · Recover the original evidence

- [ ] Locate the Instagram and Amazon CSVs, original notebooks, prediction exports, browser application shown in Figures 1.1 and 4.1–4.2, and any timing records. Ask the original contributors for missing items.
- [ ] Record source, collection date, language, sampling method, row count, duplicate count, permission to use or redistribute, and a checksum for each dataset. Keep restricted source data outside Git. Supply a shareable fixture and access instructions where needed.
- [ ] Start a claim register with one row per claim or figure. Record manuscript location, dataset version, implementation entry point, run ID, evidence path, and disposition: reproduced from original data, newly evaluated, inconclusive, or revised. A screenshot can establish what was displayed; verify its calculation separately.
- [ ] If original records cannot be recovered, freeze a new sample and publish it as a replication. Preserve the historical values separately. Never tune a replacement sample to recreate 406 or the reported timings.

## M1 · Make batch scoring reproducible

- [x] Repair the path literal in `saturn.py`, replace personal paths with arguments, share scoring across CLI, web and an appended notebook cell, and document pinned resources.
- [x] Accept `Comment` and `Review`, preserve source fields and raw text, record skip reasons, retain CSV duplicates and deduplicate connector records by ID.
- [x] Return one row per input/model with VADER thresholds, all RoBERTa probabilities, checkpoint revision and truncation flags. Current release supports the VADER–RoBERTa comparison.
- [ ] Add separate TextBlob and BERT benchmarks if the manuscript retains those comparisons. These models are outside the current two-model release.
- [x] Implement and test raw-v1, social-v1 and paper-v1 preprocessing. Preserve raw input, normalized input and profile name in exports.
- [ ] Compare preprocessing alternatives on independently labeled development data and freeze the preferred setting. Original text remains the current default.
- [x] Test CSV validation, empty batches, missing categories, ties, blanks, Unicode and long text. Verify base installation in a fresh environment and paired model repeatability in the existing environment.

**Pass condition.** Two runs on the same fixture and pinned settings produce matching labels and aggregates. Class counts sum to scored rows for each model. Scored plus skipped rows reconcile with the input.

## M2 · Connect retrieval, inference and presentation

YouTube and historical Amazon lookup passed browser acceptance on 8 November 2026. The Instagram connector is implemented and awaits successful live acceptance. All three feed the existing scoring and CSV export functions.

| URL option | Implementation task | Acceptance check |
|---|---|---|
| YouTube video · build first | Use `yt-dlp` to retrieve up to 100 top-level comments from a public video. Skip video download and record the comment sort order. [yt-dlp options](https://github.com/yt-dlp/yt-dlp#youtube) | Paste a video URL with comments enabled. Verify that the results and export contain comment text and IDs. Show whether collection reached the cap, returned zero comments, or stopped because access failed. |
| Amazon product · historical lookup | Extract the ASIN from the product link and query an indexed subset of the UCSD Amazon Reviews 2023 dataset by exact ASIN. If offering a parent-ASIN lookup, label it as covering product variants. [Dataset fields](https://amazon-reviews-2023.github.io/#data-fields) | Try one covered product and one absent from the loaded subset. Show the dataset name, review date range and matched count for the first; report the coverage gap for the second. Keep CSV import available. |
| Instagram post or Reel · optional paper demo | Use Instaloader to resolve the URL shortcode and read accessible comments with `get_comments()`. Test a permitted post first. Use a local authenticated session if required. [Instaloader documentation](https://instaloader.github.io/module/structures.html#instaloader.Post.get_comments) | Demonstrate retrieval from a permitted live post without a Meta developer app. Report login requirements, rate limits and inaccessible posts explicitly. Keep the paper’s Instagram demo pending until this route works. |

- [x] Add the URL field, supported-host validation, canonical platform IDs, source IDs/timestamps, retrieval time and Amazon dataset metadata.
- [x] Test YouTube live collection, historical Amazon matches and misses, duplicate handling, malformed inputs and collection timeouts. Export all fetched records with their scoring status.
- [ ] Complete successful live Instagram retrieval on a known accessible post and exercise an authenticated session when necessary.
- [x] Display counts, scores, distribution bars and daily UTC totals with sample counts. Export the exact records; display collection caps, warnings and a pending-request indicator. Web requests are bounded at 100 retrieved records or 1,000 uploaded rows.
- [x] Test simultaneous submissions with distinct comments and verify response isolation.

| Display or measure | Definition to implement and verify |
|---|---|
| Positive share | Positive predictions divided by scored comments, per model. |
| Net sentiment | 100 × (positive count − negative count) / scored comments. Display the signed scale from −100 to +100. For zero scored rows, show “no scored comments.” |
| Model confidence | Preserve transformer class probabilities. Test calibration on held-out labels before interpreting scores as reliability estimates. Label VADER compound as polarity strength. |
| Accuracy | Correct predictions divided by independently labeled test cases. Display the dataset and sample size alongside the result. |

**Pass condition.** Starting in the browser, analyze text, upload a CSV, then fetch a known accessible post. Trace a prediction to its source row, recompute the chart from the export, and verify error handling with an inaccessible URL. Save the demo inputs, redacted captures and run IDs.

## M3 · Evaluate quality and difficult language

- [ ] Write annotation guidelines for positive, neutral, negative, mixed and ambiguous cases, including how the last two enter the three-class evaluation. Have two people independently label test examples without seeing model predictions. Report agreement and adjudicate disagreements.
- [ ] Group repeated wording, near duplicates and comments from the same post or product before splitting. Freeze development and held-out sets. Record class and domain counts, plus counts for sarcasm, slang, emoji and negation. Label sarcasm separately if claiming sarcasm detection.
- [ ] Run all claimed models on identical test IDs. Report accuracy, macro-F1, per-class precision/recall/F1, confusion matrices and paired uncertainty intervals accounting for post/product groups. Report difficult-language slices and representative errors. If a slice is too small for a conclusion, report its size and limit the claim.
- [ ] For model confidence, compare predicted probabilities with observed correctness by confidence band. Define what “reliable” means before using that term in the conclusion. Separate predictive quality, service availability and speed.

**Pass condition.** A reviewer can regenerate each quality table from frozen labels and predictions, identify the denominator, and inspect examples where the models disagree.

## M4 · Benchmark and reconcile the manuscript

- [ ] Re-run the reported 1,000-comment comparison on identical ordered records. Record hardware, OS, dependency and checkpoint versions, input lengths, batching, warm-up and repetition count. Measure cold startup, warm inference, retrieval and browser-to-result time separately. Publish raw timings, throughput, median and 95th-percentile latency.
- [ ] Define acceptable latency, concurrency and failure rate for interactive text and bulk URL jobs before measuring. Test increasing concurrent requests, record failures and verify output isolation. Qualify “real time” with the observed workload, hardware and latency.
- [ ] Use the following figure checks when preparing the release.

| Manuscript item | Evidence required |
|---|---|
| Fig. 1.1 and Figs. 4.1–4.2 · browser input and results | Capture a fresh run from URL submission through retrieval and output. Recover the formula and input behind the historical 70% display, or label the replacement figure with its own formula and data. |
| Fig. 2.1 · VADER distributions | Recreate the Instagram and Amazon counts and percentages from row-level exports. Document rounding, skipped records and how the overall category is chosen. |
| Figs. 3.1 and 3.3 · architecture and workflow | Walk each diagram step through the released application. Mark proposed integrations explicitly. |
| Fig. 3.2 · RoBERTa | Recompute net sentiment from the saved labels. On recovered original inputs, compare against 406 across 1,000 comments (40.60%). Document any discrepancy and distinguish replication results. |
| Fig. 4.3 · preprocessing and Amazon analysis | Trace a sample review from raw text through preprocessing, model score, assigned label and exported row. |
| Section 3 · speed and accuracy comparisons | Compare measured timings against the reported roughly 60 s for RoBERTa and 30 s for VADER. Determine model-quality conclusions from M3's human-labeled comparison. |

- [x] Record application source/data hashes and runtime package versions in `results/build-manifest.json`; save browser and live-check evidence; update README setup and usage.
- [ ] Produce the final research release manifest including verified experimental results, timings and manuscript figures after the deferred studies.
- [ ] Have a second person install the release, run the fixture, exercise the web workflow and regenerate the results. Record failures and rerun affected checks after fixes.

**Completion rule.** Close each current-capability claim with linked evidence or an explicit manuscript revision. Record which historical results were reproduced, which were newly measured, and which remain unresolved. Keep future-work proposals in the roadmap.

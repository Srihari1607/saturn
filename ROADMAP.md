# SATURN roadmap

**Release objective.** A researcher can start from a clean checkout, analyze text or comments from a supported post URL, inspect and export the predictions, and regenerate the evidence behind the manuscript's results. The first live acceptance case is an authorized Instagram post because Figures 4.1–4.2 show an Instagram URL. Amazon reviews provide the second, offline domain.

**Starting point.** At commit `146157a`, the project has a VADER script with a Windows path syntax error, a pretrained RoBERTa notebook with saved output, a one-page Amazon collection script, and a static landing page. The original input CSVs, screenshot application, timing logs, and independent sentiment labels are missing from the checkout. The notebook records a net score of 406 over 1,000 comments. Historical results and fresh measurements must be tracked separately.

## Milestones and dependencies

| Milestone | Deliverable | Decision that closes the milestone |
|---|---|---|
| M0 · Recover the study | Inventory of original inputs, prediction files, notebook versions, and the application shown in the figures | Identify which figures can be reproduced from original material and which need a new experiment. Confirm access to a suitable Instagram test post. |
| M1 · Restore offline analysis | One command processes Instagram-style and Amazon-style CSVs with versioned VADER and RoBERTa models | A second person can score the example data from a clean checkout. Every input row is accounted for. |
| M2 · Deliver the web workflow | Pasted text, CSV upload, and an authorized post URL lead to inspectable results, a distribution chart, a time trend where timestamps exist, and an export | Demonstrate a live fetch and match the displayed totals to the downloaded rows. Record the platform, access conditions and limits. |
| M3 · Evaluate the research claims | Frozen datasets, human labels, paired model predictions, and accuracy, calibration and language-pattern results | Document which model performs better on which domain and with what uncertainty. Qualify claims where evidence is inconclusive. |
| M4 · Measure end-to-end performance | Timings for 1,000 comments, repeated single-request and concurrent runs, plus a reproducible release package | Rebuild each retained figure or table and link each conclusion to a measured result. Another person completes the demo and evaluation from the release instructions. |

**Sequence.** Begin M0 first. If recovery takes time, start M1 with a clearly identified demonstration fixture. Begin annotation for M3 as soon as dataset provenance and the split are settled. M2 and M3 can proceed independently after M1. Benchmark the final integrated configuration in M4.

**Scope decisions.** A CSV-only release can support offline comparison. A successful demonstration on another platform can support a newly scoped URL workflow. Keep the original Instagram URL claim open until that route is demonstrated. Apply the same rule to every additional platform named as operational. A claim may be narrowed in the manuscript, with the reason recorded.

## After the paper-aligned release

| Use case | Next capability | Evidence needed to adopt it |
|---|---|---|
| Product feedback | Separate sentiment about product aspects such as battery, camera and delivery | Compare aspect extraction and sentiment with human labels on mixed-opinion reviews. |
| Kannada–English comments | Compare direct multilingual classification with translation followed by classification | Use a bilingual-labeled test set. Report results for Kannada script, Romanized Kannada and mixed text separately. |
| Brand monitoring | Schedule collection and flag sustained changes in negative sentiment | Replay timestamped data and measure missed events, false alerts and detection delay. |
| Support triage | Route uncertain or disputed cases to a reviewer and capture corrections | Evaluate actionable-complaint recall and reviewer workload on a later batch. |

The paper also proposes emotion categories, adaptive learning, more platform connectors and distributed or edge processing. Prioritize these against a demonstrated user need or measured bottleneck after M4.

Use the [implementation plan](plan.md) for the tasks, figure checks and release criteria.

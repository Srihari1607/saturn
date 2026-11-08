"""Pinned resources and offline inference for the SATURN comparison."""
import argparse
import hashlib
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent / ".resources"
LEXICON = ROOT / "vader_lexicon.zip"
LEXICON_URL = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/sentiment/vader_lexicon.zip"
LEXICON_HASH = "8adba4294eef3964d820bf655e37e61bdc3a341994356af59b74fb3b4a36ce5c"
MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
REVISION = "daefdd1f6ae931839bce4d0f3db0a1a4265cd50f"
LABELS = ("Negative", "Neutral", "Positive")


def check_lexicon(data):
    if hashlib.sha256(data).hexdigest() != LEXICON_HASH:
        raise ValueError("VADER lexicon checksum mismatch.")


def install(name):
    ROOT.mkdir(exist_ok=True)
    if name == "roberta":
        from huggingface_hub import snapshot_download
        snapshot_download(MODEL, revision=REVISION, local_dir=ROOT / REVISION,
                          allow_patterns=["config.json", "merges.txt", "vocab.json",
                                          "special_tokens_map.json", "pytorch_model.bin"])
        return
    with urlopen(LEXICON_URL, timeout=45) as response:
        data = response.read()
    check_lexicon(data)
    with tempfile.NamedTemporaryFile(dir=ROOT, delete=False) as temp:
        temp.write(data)
    os.replace(temp.name, LEXICON)


@lru_cache(maxsize=2)
def scorer(name):
    if name == "vader":
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        if not LEXICON.is_file():
            raise RuntimeError("Set up VADER with: python models.py vader")
        check_lexicon(LEXICON.read_bytes())
        analyzer = SentimentIntensityAnalyzer(
            lexicon_file=(LEXICON.resolve().as_uri() + "/vader_lexicon/vader_lexicon.txt")
        )

        def predict(text):
            score = analyzer.polarity_scores(text)["compound"]
            label = "Positive" if score >= 0.05 else "Negative" if score <= -0.05 else "Neutral"
            return {"label": label, "compound": score}
        return predict

    if name != "roberta":
        raise ValueError("Unknown model.")
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch
    path = ROOT / REVISION
    if not (path / "pytorch_model.bin").exists():
        raise RuntimeError("Set up RoBERTa with: python models.py roberta")
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True).eval()
    if [model.config.id2label[i] for i in range(3)] != ["LABEL_0", "LABEL_1", "LABEL_2"]:
        raise ValueError("Unexpected label mapping for the pinned checkpoint.")

    def predict(text):
        ids = tokenizer.encode(text, add_special_tokens=False, verbose=False)
        limit = 512 - tokenizer.num_special_tokens_to_add(pair=False)
        # Encode the original text with the checkpoint's standard boundary tokens.
        inputs = tokenizer(text, truncation=True, max_length=512, return_tensors="pt")
        with torch.inference_mode():
            probabilities = model(**inputs).logits.softmax(dim=-1)[0].tolist()
        winner = max(range(3), key=probabilities.__getitem__)
        return {"label": LABELS[winner], "truncated": len(ids) > limit,
                **{f"p_{label.lower()}": p for label, p in zip(LABELS, probabilities)}}
    return predict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download pinned SATURN resources")
    parser.add_argument("model", choices=["vader", "roberta"])
    install(parser.parse_args().model)

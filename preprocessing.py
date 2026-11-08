"""Versioned text transformations; raw input is retained in every export."""
import re

PROFILES = ("raw-v1", "social-v1", "paper-v1")
# Explicit small stop list for the paper variant; negation remains meaningful.
STOP_WORDS = frozenset("a an the is are was were be been being of to in on at for and or with".split())


def preprocess(text, profile):
    if profile not in PROFILES:
        raise ValueError("Unknown preprocessing profile.")
    if profile == "raw-v1":
        return text
    import emoji
    text = emoji.replace_emoji(text, replace=lambda chars, data:
                              " " + emoji.demojize(chars).strip(":").replace("_", " ") + " ")
    text = re.sub(r"https?://\S+", "http" if profile == "social-v1" else "", text)
    text = re.sub(r"(?<!\w)@\w+", "@user" if profile == "social-v1" else "", text)
    text = re.sub(r"#(\w+)", r"\1", text)
    if profile == "paper-v1":
        text = " ".join(word for word in text.lower().split() if word not in STOP_WORDS)
    return " ".join(text.split())

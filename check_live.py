"""Record live connector outcomes without substituting demonstration comments."""
import json
from pathlib import Path
from time import perf_counter

from connectors import collect


def main():
    results = []
    for url in ["https://www.youtube.com/watch?v=jNQXAC9IVRw",
                "https://www.amazon.com/dp/B0742LVLMJ",
                "https://www.amazon.com/dp/B000000000"]:
        start = perf_counter()
        try:
            result = collect(url, limit=5)
            report = {"url": url, "count": len(result["records"]), "details": result["details"],
                      "warnings": result["warnings"], "limited": result["limited"]}
        except (RuntimeError, ValueError) as error:
            report = {"url": url, "error": str(error)}
        report["seconds"] = round(perf_counter() - start, 2)
        results.append(report)
        print(json.dumps(report), flush=True)
    output = Path(__file__).parent / "results"
    output.mkdir(exist_ok=True)
    (output / "live-checks.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

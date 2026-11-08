"""Exercise the real local server in Chromium and save a visual check."""
import json
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from app import app


def main():
    root = Path(__file__).resolve().parent
    output = root / "results"
    output.mkdir(exist_ok=True)
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    address = f"http://127.0.0.1:{server.server_port}"
    checks = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 900})
            page.set_default_timeout(120000)
            page.goto(address)
            page.locator("#text").fill("I love this camera!")
            page.get_by_role("button", name="Analyze sentiment").click()
            page.get_by_text("0.6696 polarity").wait_for()
            checks.append("Text submission and real VADER result")

            page.goto(address)
            page.locator("#file").set_input_files(root / "examples" / "demo.csv")
            page.get_by_role("button", name="Analyze sentiment").click()
            page.get_by_role("heading", name="Daily sentiment").wait_for()
            with page.expect_download() as download:
                page.get_by_role("link", name="Download predictions").click()
            download.value.save_as(output / "browser-predictions.csv")
            checks.append("CSV upload, daily trends and download")

            page.goto(address)
            page.locator("#url").fill("https://www.amazon.com/dp/B0742LVLMJ")
            page.get_by_role("button", name="Analyze sentiment").click()
            page.get_by_text("Collection details", exact=True).click()
            page.get_by_text("100 records retrieved", exact=False).wait_for()
            page.screenshot(path=output / "amazon-desktop.png")
            checks.append("Amazon URL retrieves 100 historical reviews")
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Page overflows on mobile"
            page.screenshot(path=output / "amazon-mobile.png")
            checks.append("390px mobile layout has no horizontal page overflow")

            page.goto(address)
            page.locator("#url").fill("https://www.amazon.com/dp/B000000000")
            page.get_by_role("button", name="Analyze sentiment").click()
            page.get_by_text("Collection details", exact=True).click()
            page.get_by_text("No matching reviews in the loaded dataset.").wait_for()
            checks.append("Absent product reports dataset coverage gap")
            page.goto(address)
            page.locator("#url").fill("https://www.youtube.com/watch?v=jNQXAC9IVRw")
            page.get_by_role("button", name="Analyze sentiment").click()
            page.get_by_role("heading", name="Me at the zoo", exact=True).wait_for()
            page.get_by_role("heading", name="Overall comment summary", exact=True).wait_for()
            page.get_by_text("Collection details", exact=True).click()
            page.get_by_text("100 records retrieved", exact=False).wait_for()
            with page.expect_download() as download:
                page.get_by_role("link", name="Download predictions").click()
            download.value.save_as(output / "youtube-predictions.csv")
            page.screenshot(path=output / "youtube-mobile.png")
            checks.append("Live YouTube URL retrieves and scores 100 comments with a downloadable CSV")
            page.goto(address)
            page.locator("#url").fill("https://example.com/")
            page.get_by_role("button", name="Analyze sentiment").click()
            page.get_by_role("alert").wait_for()
            checks.append("Unsupported URL produces a visible validation error")
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    (output / "browser-checks.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

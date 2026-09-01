"""
Signal 2 (REQUIRED): Real browser automation via Playwright.
Launches headless Chromium, navigates to a search engine results page
for the company, and extracts rendered result snippets. This is genuine
browser automation - not a plain HTTP call - because it executes JS,
waits for dynamic content, and interacts with the page like a real browser.
"""
from playwright.sync_api import sync_playwright


def get_browser_signal(company_name: str) -> dict:
    """
    Uses headless Chromium to search Bing (less bot-restrictive than Google
    for automation) for the company and extract rendered result titles/snippets.
    """
    if not company_name:
        return {"error": "no company name provided"}

    result = {
        "search_query": f"{company_name} company",
        "result_titles": [],
        "result_snippets": [],
        "error": None,
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ))

            query = f"{company_name} company"
            page.goto(f"https://www.bing.com/search?q={query}", timeout=20000)
            page.wait_for_selector("li.b_algo", timeout=10000)

            titles = page.locator("li.b_algo h2").all_text_contents()
            snippets = page.locator("li.b_algo .b_caption p").all_text_contents()

            result["result_titles"] = titles[:5]
            result["result_snippets"] = [s.strip()[:300] for s in snippets[:5]]

            browser.close()

    except Exception as e:
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    import json
    print(json.dumps(get_browser_signal("Stripe"), indent=2))
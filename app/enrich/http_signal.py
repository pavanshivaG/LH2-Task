"""
Signal 1: Plain HTTP call.
Checks if the company's domain resolves and is reachable, and pulls
basic metadata (status code, title tag, response time) via a simple
GET request - no browser rendering involved.
"""
import httpx
import time
import re


def get_http_signal(domain: str) -> dict:
    """
    Given a bare domain (e.g. 'stripe.com'), returns a dict of basic
    HTTP-level signals about the company's website.
    """
    if not domain:
        return {"error": "no domain provided"}

    url = domain if domain.startswith("http") else f"https://{domain}"

    result = {
        "url": url,
        "reachable": False,
        "status_code": None,
        "response_time_ms": None,
        "title": None,
        "error": None,
    }

    try:
        start = time.time()
        with httpx.Client(follow_redirects=True, timeout=10.0) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 (company-intel-agent)"})
        elapsed_ms = round((time.time() - start) * 1000, 2)

        result["reachable"] = resp.status_code < 400
        result["status_code"] = resp.status_code
        result["response_time_ms"] = elapsed_ms

        title_match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
        if title_match:
            result["title"] = title_match.group(1).strip()[:200]

    except Exception as e:
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    import json
    print(json.dumps(get_http_signal("stripe.com"), indent=2))
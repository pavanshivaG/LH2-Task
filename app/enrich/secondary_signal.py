"""
Signal 3: Secondary independent HTTP signal.
Queries the Hacker News Algolia Search API for mentions of the company -
a free, no-key-required API that gives a rough signal of tech-community
visibility/buzz.
"""
import httpx

HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"


def get_secondary_signal(company_name: str) -> dict:
    """
    Returns HN mention count and top hit titles for a company name.
    """
    if not company_name:
        return {"error": "no company name provided"}

    result = {
        "hn_mention_count": 0,
        "top_titles": [],
        "error": None,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(HN_ALGOLIA_URL, params={"query": company_name, "tags": "story"})
        resp.raise_for_status()
        data = resp.json()

        result["hn_mention_count"] = data.get("nbHits", 0)
        result["top_titles"] = [
            hit.get("title") for hit in data.get("hits", [])[:5] if hit.get("title")
        ]

    except Exception as e:
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    import json
    print(json.dumps(get_secondary_signal("Stripe"), indent=2))
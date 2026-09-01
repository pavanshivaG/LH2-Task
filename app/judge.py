"""
The LLM Judge: takes all enrichment signals for a company and produces
a structured verdict via reasoning over the evidence - not a summary.
"""
import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in .env")

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.6-flash"

JUDGE_PROMPT_TEMPLATE = """You are a rigorous B2B company-fit analyst. You will be given
raw signals about a company gathered from independent sources. Your job is to REASON
over this evidence and produce a structured verdict - not summarize the inputs.

Company name: {company_name}
Domain: {domain}

--- SIGNAL 1: Website reachability (plain HTTP check) ---
{http_signal}

--- SIGNAL 2: Search engine presence (real browser automation) ---
{browser_signal}

--- SIGNAL 3: Hacker News / tech-community mentions ---
{secondary_signal}

Based on genuine reasoning over this evidence (e.g. cross-checking whether the
website is live and legitimate, whether search results corroborate a real
operating company, whether tech-community buzz suggests scale or relevance),
decide:

1. fit_verdict: one of "Strong Fit", "Possible Fit", "Weak Fit", "No Fit" -
   your judgment of whether this looks like a legitimate, active, and
   relevant company worth engaging with.
2. confidence: a float between 0.0 and 1.0 reflecting how confident you are
   in this verdict given the evidence quality/consistency.
3. follow_up_question: ONE specific, evidence-grounded question a human
   analyst should investigate next to resolve remaining uncertainty.
4. reasoning: 2-4 sentences explaining WHY you reached this verdict, citing
   specific evidence points (not a generic restatement).

Respond with ONLY valid JSON, no markdown fences, no preamble, in this exact shape:
{{
  "fit_verdict": "...",
  "confidence": 0.0,
  "follow_up_question": "...",
  "reasoning": "..."
}}
"""


def _extract_json(text: str) -> dict:
    """Strip markdown fences if present and parse JSON safely."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


def judge_company(company_name: str, domain: str, http_signal: dict,
                   browser_signal: dict, secondary_signal: dict) -> dict:
    """
    Feeds all three signals to Gemini and returns a structured verdict dict.
    """
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        company_name=company_name,
        domain=domain,
        http_signal=json.dumps(http_signal, indent=2),
        browser_signal=json.dumps(browser_signal, indent=2),
        secondary_signal=json.dumps(secondary_signal, indent=2),
    )

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)

    raw_text = response.text
    try:
        verdict = _extract_json(raw_text)
    except (json.JSONDecodeError, AttributeError) as e:
        verdict = {
            "fit_verdict": "Error",
            "confidence": 0.0,
            "follow_up_question": "N/A - LLM response could not be parsed",
            "reasoning": f"Failed to parse LLM output: {e}. Raw: {raw_text[:300]}",
        }

    return verdict


if __name__ == "__main__":
    # Quick manual test with dummy signals
    test_verdict = judge_company(
        company_name="Stripe",
        domain="stripe.com",
        http_signal={"reachable": True, "status_code": 200, "title": "Stripe | Financial Infrastructure"},
        browser_signal={"result_titles": ["Stripe | Financial Infrastructure to Grow Your Revenue", "Stripe, Inc. - Wikipedia"]},
        secondary_signal={"hn_mention_count": 15514},
    )
    print(json.dumps(test_verdict, indent=2))
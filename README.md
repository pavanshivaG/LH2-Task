# LH2-Task — Company Intelligence Agent

An end-to-end, self-running pipeline that reads companies from a Google Sheet, enriches each one with independent signals (including real browser automation), persists the results to a Postgres database, judges fit using an LLM, and syncs the verdict back to the Sheet — fully containerized, deployed, and wired to run on its own via GitHub Actions.

**Live URL:** https://company-intelligence-agent-xrq7.onrender.com

---

## Architecture

Google Sheet (source of truth for company list)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼
FastAPI app (`app/main.py`)
- APScheduler → runs pipeline every 30 min automatically
- `POST /trigger` → run pipeline on demand
- `GET /status` → last run summary
- `GET /companies` → all processed records
- `GET /companies/{id}` → full detail incl. raw signals

Pipeline (`app/pipeline.py`):
1. Read unprocessed rows from Sheet (`app/sheets.py`)
2. Enrich each company with 3 independent signals:
   - `app/enrich/http_signal.py` → plain HTTP GET, status/title check
   - `app/enrich/browser_signal.py` → Playwright headless Chromium, real browser automation, JS-rendered search results
   - `app/enrich/secondary_signal.py` → HN Algolia API, tech-community buzz
3. Judge (`app/judge.py`) → Gemini LLM reasons over all 3 signals together, returns structured JSON: `fit_verdict`, `confidence`, `follow_up_question`, `reasoning`
4. Persist to Postgres (Supabase) — `app/db/models.py`, `app/db/database.py`
5. Sync verdict back to the Sheet (authenticated via Google service account)

## Why this satisfies each requirement

| Requirement | How it's met |
|---|---|
| Source updates without restart | The Sheet is re-read fresh on every `/trigger` call or scheduled tick — no server restart needed to pick up new rows |
| Real browser automation | `browser_signal.py` launches actual headless Chromium via Playwright, navigates a search engine results page, and scrapes JS-rendered content |
| Real database | Supabase-hosted Postgres, accessed via SQLAlchemy — not in-memory, not the Sheet itself |
| LLM reasoning, not summary | The judge prompt explicitly asks Gemini to cross-reference the 3 independent signals against each other and justify a verdict, not restate them |
| Authenticated sync back | Google service account with Editor access to the specific Sheet, scoped credentials only |
| Self-running | APScheduler runs the pipeline every 30 min inside the deployed app; `/trigger` and `/status` allow on-demand control and inspection |
| Shipped | Dockerfile based on `mcr.microsoft.com/playwright/python` (Chromium deps pre-installed), deployed on Render's free tier |
| GitHub wiring | `.github/workflows/ci.yml` runs on every push (installs deps, compiles code, builds Docker image); `.github/workflows/scheduled-trigger.yml` runs on a 6-hour cron and hits the live `/trigger` endpoint with zero human involvement |

## Tech stack (all free-tier)

- **Language:** Python 3.12
- **API framework:** FastAPI + Uvicorn
- **Scheduler:** APScheduler (in-process)
- **Browser automation:** Playwright (headless Chromium)
- **Database:** Supabase (free Postgres), accessed via SQLAlchemy + psycopg2
- **LLM:** Google Gemini (`gemini-3.6-flash`) via `google-generativeai`
- **Sheet access:** Google Sheets API + Drive API via a service account (`gspread`)
- **Container:** Docker, based on Playwright's official Python image
- **Hosting:** Render (free web service, Docker deploy)
- **CI/CD:** GitHub Actions (build check on push, scheduled autonomous trigger)

## Project structure

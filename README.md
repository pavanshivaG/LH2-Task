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

## Requirements

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


LH2-Task/
├── app/
│ ├── main.py # FastAPI app, endpoints, scheduler
│ ├── pipeline.py # Orchestrates enrich -> persist -> judge -> sync
│ ├── sheets.py # Google Sheets read/write layer
│ ├── judge.py # LLM judgment logic
│ ├── enrich/
│ │ ├── http_signal.py # Signal 1: plain HTTP
│ │ ├── browser_signal.py # Signal 2: Playwright browser automation
│ │ └── secondary_signal.py # Signal 3: HN Algolia API
│ └── db/
│ ├── models.py # SQLAlchemy ORM models
│ └── database.py # Engine/session setup
├── .github/workflows/
│ ├── ci.yml # Runs on every push
│ └── scheduled-trigger.yml # Runs every 6h, no human involved
├── Dockerfile
├── requirements.txt
├── reset_db.py # Dev utility: drop + recreate tables on schema change
├── test_sheets_connection.py # Manual smoke test for Sheets auth
└── test_db_connection.py # Manual smoke test for DB connection




## Environment variables

See `.env.example`. Required:

- `GOOGLE_SHEET_ID` — the target Sheet's ID
- `GOOGLE_SERVICE_ACCOUNT_FILE` — path to service account JSON (local dev)
- `GOOGLE_SERVICE_ACCOUNT_JSON` — full JSON content as a string (used in deployment; written to disk at startup by `app/main.py`)
- `DATABASE_URL` — Postgres connection string (Supabase pooler recommended)
- `GEMINI_API_KEY` — Google AI Studio API key

## Running locally

```bash
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
playwright install chromium

cp .env.example .env   # fill in real values

python -m app.pipeline          # run the pipeline once, standalone
uvicorn app.main:app --reload   # or run the full API + scheduler
```

## Running with Docker

```bash
docker build -t lh2-task .
docker run -p 8000:8000 --env-file .env lh2-task
```

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/trigger` | Run the pipeline immediately |
| GET | `/status` | Summary of the most recent run |
| GET | `/companies` | All processed company records |
| GET | `/companies/{id}` | Full detail for one company, including raw signals |

## Notes 

- Render's free tier spins down after inactivity; the scheduled GitHub Action helps keep it warm and guarantees periodic execution regardless.
- `gemini-3.6-flash` is used since earlier model names (e.g. `gemini-2.0-flash`) were deprecated during development — model availability should be re-checked periodically via the Gemini API.
- The browser automation signal targets Bing's search results page (less bot-restrictive than Google for lightweight automation); this could be swapped for direct company-page scraping if a more source-specific signal is preferred.

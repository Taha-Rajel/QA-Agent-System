# QA Agent System

Autonomous website QA: give it a URL, a team of agents tests the site in a real browser, and you get an HTML report with screenshots and fix suggestions.

```text
Enter a URL → agents test the site → screenshots + results collected → report generated
```

## Table of contents

- [Features](#features)
- [How it works](#how-it-works)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Agents](#agents)
- [Project structure](#project-structure)
- [Reports and history](#reports-and-history)
- [Extending the project](#extending-the-project)
- [Troubleshooting](#troubleshooting)
- [Limitations and roadmap](#limitations-and-roadmap)
- [Design decisions](#design-decisions)

## Features

- Test any site from the **web dashboard** or the **CLI**
- Real Chromium browser driven by **Playwright** (visible or headless)
- Specialized agents: UI, navigation, authentication, forms, visual review, corrections
- **AI vision review** of screenshots through OpenRouter
- Screenshot evidence for every important state
- Generated **HTML report** with pass/fail totals and correction guidance
- Run history stored in a simple JSON file

## How it works

```text
Web UI / CLI
   └─ main.run(url)
        ├─ launch Chromium (tools/browser_tool.py)
        ├─ Orchestrator runs the agents in order
        │    Website Description → UI → Auth → Navigation → Forms → Correction
        │    (UI, Auth and Forms call the Visual agent → OpenRouter vision model)
        ├─ report_builder: totals + save to db/qa_history.json
        └─ html_report: output/report_<timestamp>.html
```

Every agent returns a list of `TestResult` objects (`agent`, `test_name`, `status`, `detail`, `screenshot_path`, `duration_ms`), so the orchestrator, the API and the report all work with the same shape. Statuses: `PASS`, `FAIL`, `ERROR`, `INFO`.

**Tech stack:** Python 3.10+, Playwright, FastAPI + Uvicorn, Pydantic, Jinja2, python-dotenv, OpenRouter (vision), plain HTML/CSS/JS for the dashboard.

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies and the browser
pip install -r requirements.txt
python -m playwright install chromium

# 3. Configure
cp env_example .env              # Windows: copy .env.example .env
# then edit .env (see Configuration)

# 4. Run
python main.py                    # CLI, uses TARGET_URL from .env
uvicorn app:app --reload          # or the web dashboard
```


## Configuration

Settings live in `.env` (git-ignored) and are loaded by `config.py`.

| Variable | Required | Description |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | For visual checks | API key for OpenRouter |
| `OPENROUTER_MODEL` | No | Vision model. Default: `nvidia/nemotron-nano-12b-v2-vl:free` |
| `TARGET_URL` | CLI only | Site to test when running `python main.py` |
| `TEST_EMAIL` / `TEST_PASSWORD` | No | Credentials for the auth agent. If a login form exists and these are empty, random ones are generated |
| `PLAYWRIGHT_HEADLESS` | No | `false` (default) to watch Chromium, `true` for background runs |

Other constants (timeouts, mobile viewport 375×812, output paths) are in `config.py`.

**Never commit `.env` or share it in a zip/archive.** If a key was ever shared, revoke it and create a new one.

## Usage

### Web dashboard

```bash
uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>, enter a URL, click **Test**, then open the generated report.

| Endpoint | Description |
| --- | --- |
| `GET /` | Dashboard |
| `POST /api/test-runs` | Start a QA run with `{"url": "https://..."}` |
| `GET /api/runs` | Last runs from the history |

Only one run can be active at a time; a second request gets `409`.

### CLI

```bash
python main.py
```

The terminal logs each step (browser launch, agent start/finish, report path). The report is written to `output/`.

## Agents

| Agent | File | What it checks |
| --- | --- | --- |
| Website Description | `agents/website_description_agent.py` | Title, headings, forms, buttons, links → short `INFO` summary of the site |
| UI | `agents/ui_agent.py` | Homepage screenshot, visible buttons/controls, theme toggle, mobile layout (375 px) |
| Auth | `agents/auth_agent.py` | Valid login, wrong login, logout, protected route. Skipped cleanly if no login form |
| Navigation | `agents/navigation_agent.py` | Up to 20 internal links, HTTP status, console errors, back / forward / refresh |
| Forms | `agents/form_agent.py` | Empty submit, filled submit with generic data, visual review of the result |
| Visual | `agents/visual_agent.py` | Sends a screenshot to the vision model → `PASS`/`FAIL` + reason |
| Correction | `agents/correction_agent.py` | Turns failures into `INFO` rows with fix guidance |

`agents/orchestrator.py` only controls the order and collects results. `agents/helpers.py` provides `result(...)` and `fail(...)` to build `TestResult` objects consistently.

## Project structure

```text
qa-agent-system/
├── app.py                  FastAPI server (dashboard + API)
├── main.py                 CLI entry point and shared run() function
├── config.py               Environment variables, paths, timeouts
├── models.py               Pydantic models: TestResult, VisualLog, RunRecord
├── requirements.txt
├── agents/                 QA logic (one agent per responsibility) + orchestrator
├── tools/                  Reusable wrappers: browser, screenshot, interaction, DOM, vision, log
├── reports/                report_builder.py (data) and html_report.py (rendering)
├── db/                     database.py (JSON read/write), queries.py (history API)
├── web/                    Dashboard: index.html, app.js, styles.css
├── tests/                  Test definitions per agent (not pytest yet)
├── screenshots/runs/       Screenshots, one folder per run (generated)
├── output/                 HTML reports (generated)
└── docs/                   Extra documentation, e.g. PRESENTATION.md
```

### Tools

| Tool | Role |
| --- | --- |
| `browser_tool.py` | `launch_browser()`, `navigate()` (waits for `networkidle`), `close_browser()` |
| `screenshot_tool.py` | `full_page_shot()`, `element_shot()` → `screenshots/runs/<timestamp>/` |
| `interaction_tool.py` | `click`, `type_text`, `hover`, `scroll_to`; each returns `True`/`False` |
| `dom_tool.py` | `get_all_links`, `element_exists`, `get_text`, `wait_for` |
| `vision_tool.py` | Base64-encodes a screenshot and calls OpenRouter |
| `log_tool.py` | `log_step()` terminal logger |

## Reports and history

**HTML report** (`output/report_<timestamp>.html`): run ID, target URL, timestamp, pass/fail/info counts, duration, results grouped by agent, screenshot thumbnails, correction guidance.

**History** (`db/qa_history.json`):

```json
{ "runs": [], "tests": [], "visuals": [] }
```

`db/database.py` reads/writes the file; `db/queries.py` exposes `insert_run`, `insert_test`, `insert_visual`, `get_last_runs`, `get_failures`, `get_all_failures_by_test`. The rest of the app only uses `queries.py`, so the storage can later be replaced (e.g. SQLite) without touching agents.

## Extending the project

**New agent**
1. Create `agents/my_agent.py` with a class that has `name = "MyAgent"` and an `async run()` returning `list[TestResult]`.
2. Register it in `agents/orchestrator.py`.

**New tool:** add a small focused helper in `tools/` that does one thing, logs the action and returns success/failure.

**New report field:** compute it in `reports/report_builder.py`, render it in `reports/html_report.py`, store it via `db/queries.py` if it belongs in the history.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Old URL still tested | `.env` was edited but not saved. Save it and check `TARGET_URL` |
| "Executable doesn't exist" | `python -m playwright install chromium` |
| Vision checks fail | Check `OPENROUTER_API_KEY`, internet access, and that the model supports images |
| Auth tests skipped | Expected when the site has no login form |
| Run is slow | `networkidle` waits, vision model latency, and up to 20 pages visited |

## Limitations and roadmap

**Current limitations**
- Generic form filling and simple login detection
- Visual verdicts depend on the vision model
- Navigation visits at most 20 internal links
- Corrections are rule-based
- JSON history does not scale to large datasets
- `tests/` files are definitions, not executable pytest tests

**Roadmap**
- PDF export and report filtering
- Scheduled runs, email/Slack notifications
- Accessibility and performance checks
- Screenshot comparison between runs
- Custom test scenarios per website
- CI/CD integration (GitHub Actions / GitLab CI)
- SQLite or another real database

## Design decisions

- **JSON instead of SQLite:** easy to inspect and reset for a first version; `db/queries.py` isolates the storage so it can change later.
- **No memory/vector layer yet:** useful later, not needed for a working first version.
- **Tools instead of raw Playwright calls:** consistent waiting, logging and return values.
- **Agents with one responsibility each:** easier to read, test and extend.

---

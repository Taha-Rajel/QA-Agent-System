"""FastAPI web app for the QA Agent System interface."""

import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import BASE_DIR, OUTPUT_DIR
from db.queries import get_last_runs
from main import run as run_qa
from tools.log_tool import log_step


WEB_DIR = BASE_DIR / "web"
RESULT_CATEGORY_ORDER = ["UI", "Navigation", "Forms", "Auth"]
SOLUTION_AGENT = "Correction"

app = FastAPI(title="QA Agent System", version="1.0.0")
run_lock = asyncio.Lock()

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
app.mount("/reports", StaticFiles(directory=OUTPUT_DIR, check_dir=False), name="reports")
app.mount("/screenshots", StaticFiles(directory=BASE_DIR / "screenshots", check_dir=False), name="screenshots")


class TestRunRequest(BaseModel):
    url: str


def normalize_target_url(value: str) -> str:
    """Return a usable HTTP(S) URL or raise a request error."""
    target = value.strip()
    if not target:
        raise HTTPException(status_code=422, detail="Website URL is required.")
    if "://" not in target:
        target = f"https://{target}"

    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Enter a valid http or https URL.")
    return target


def _create_browser_event_loop() -> asyncio.AbstractEventLoop:
    """Create an event loop that can launch Playwright subprocesses."""
    if sys.platform == "win32" and hasattr(asyncio, "ProactorEventLoop"):
        return asyncio.ProactorEventLoop()
    return asyncio.new_event_loop()


def run_qa_in_browser_loop(target_url: str) -> dict:
    """Run the QA workflow on a Playwright-compatible event loop."""
    loop = _create_browser_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run_qa(target_url=target_url))
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            asyncio.set_event_loop(None)
            loop.close()


def serialize_test_result(item, index: int) -> dict:
    """Return a browser-friendly representation of an agent result."""
    return {
        "id": f"TC_{index:03d}",
        "agent": item.agent,
        "category": item.agent,
        "test_name": item.test_name,
        "status": item.status,
        "detail": item.detail,
        "duration_ms": item.duration_ms,
        "screenshot_path": item.screenshot_path,
    }


def serialize_solution(item, index: int) -> dict:
    """Return correction guidance for the Solutions panel."""
    title = item.test_name
    if title.lower().startswith("fix "):
        title = f"Fix {title[4:]}"

    return {
        "test_id": f"FIX_{index:03d}",
        "title": title,
        "description": item.detail,
        "effort": "Medium",
        "impact": "High",
        "status": item.status,
        "screenshot_path": item.screenshot_path,
    }


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = WEB_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return Response(status_code=204)


@app.get("/api/runs")
async def recent_runs():
    return {"runs": get_last_runs(6)}


@app.post("/api/test-runs")
async def create_test_run(payload: TestRunRequest):
    target_url = normalize_target_url(payload.url)

    if run_lock.locked():
        raise HTTPException(status_code=409, detail="A QA run is already in progress.")

    try:
        async with run_lock:
            run_result = await asyncio.to_thread(run_qa_in_browser_loop, target_url)
    except HTTPException:
        raise
    except Exception as exc:
        log_step(f"QA run failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    report_path = Path(run_result["report_path"])
    report_data = run_result["report_data"]
    test_items = [item for item in report_data["results"] if item.agent != SOLUTION_AGENT]
    solution_items = [item for item in report_data["results"] if item.agent == SOLUTION_AGENT]
    failures = [
        {
            "agent": item.agent,
            "test_name": item.test_name,
            "status": item.status,
            "detail": item.detail,
        }
        for item in test_items
        if item.status in {"FAIL", "ERROR"}
    ]
    categories = []
    for agent_name in RESULT_CATEGORY_ORDER:
        items = [item for item in test_items if item.agent == agent_name]
        counted_items = [item for item in items if item.status in {"PASS", "FAIL", "ERROR"}]
        categories.append(
            {
                "name": agent_name,
                "total": len(counted_items),
                "pass": sum(1 for item in counted_items if item.status == "PASS"),
                "fail": sum(1 for item in counted_items if item.status in {"FAIL", "ERROR"}),
            }
        )

    total_pass = sum(1 for item in test_items if item.status == "PASS")
    total_fail = sum(1 for item in test_items if item.status in {"FAIL", "ERROR"})
    total_info = sum(1 for item in test_items if item.status == "INFO")

    return {
        "status": "completed",
        "run_id": report_data["run_id"],
        "target_url": report_data["target_url"],
        "report_url": f"/reports/{report_path.name}",
        "summary": {
            "total": len(test_items),
            "pass": total_pass,
            "fail": total_fail,
            "info": total_info,
            "duration_ms": sum(item.duration_ms for item in test_items),
        },
        "categories": categories,
        "failures": failures,
        "tests": [serialize_test_result(item, index) for index, item in enumerate(test_items, start=1)],
        "solutions": [serialize_solution(item, index) for index, item in enumerate(solution_items, start=1)],
    }

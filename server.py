"""Web app for the Public Sentiment Analyzer (FastAPI).

Run:  python server.py   ->  http://127.0.0.1:8000   (API docs at /docs)
Uses the same reddit.db as the CLI. "Refresh" runs the same pipeline as CLI option 2.
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
os.chdir(BASE)  # the DB path is relative, so always work from the project folder

import web_report  # noqa: E402
from schemas import RefreshStatus, TopicReport, TopicSummary  # noqa: E402

app = FastAPI(title="Public Sentiment Analyzer")

if (BASE / "static").is_dir():
    app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

# Same steps, same order as app.py option 2
PIPELINE = [
    ("reset_db.py", "Resetting DB"),
    ("fetch_rising.py", "Fetching trending posts"),
    ("fetch_comments.py", "Fetching comments"),
    ("extract_post_entities.py", "Extracting topic entities"),
    ("clear_entity_stance.py", "Clearing stance table"),
    ("analyze_entity_stance_auto.py", "Analyzing entity stance"),
    ("analyze_topic_stance.py", "Analyzing topic stance"),
]

job = {"running": False, "step": 0, "label": "", "error": None, "finished_at": None}
lock = threading.Lock()


def run_pipeline():
    """Runs in a worker thread so the site stays responsive during a refresh."""
    try:
        for i, (script, label) in enumerate(PIPELINE, start=1):
            job.update(step=i, label=label)
            proc = subprocess.run([sys.executable, script], cwd=BASE, capture_output=True, text=True)
            if proc.returncode != 0:
                tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-5:]
                job["error"] = f"{script} failed: " + " | ".join(tail)
                return
    except Exception as exc:  # noqa: BLE001
        job["error"] = str(exc)
    finally:
        job.update(running=False, finished_at=int(time.time()))


@app.get("/", include_in_schema=False)
def index():
    page = BASE / "templates" / "index.html"
    if page.exists():
        return FileResponse(page)
    return JSONResponse({"message": "Frontend not built yet. API docs are at /docs"})


@app.get("/api/topics", response_model=list[TopicSummary])
def api_topics():
    return web_report.list_topics()


@app.get("/api/topics/{n}", response_model=TopicReport)
def api_topic(n: int):
    report = web_report.build_report(n)
    if report is None:
        raise HTTPException(status_code=404, detail="No such topic")
    return report


@app.post("/api/refresh", status_code=202)
def api_refresh(background: BackgroundTasks):
    with lock:
        if job["running"]:
            raise HTTPException(status_code=409, detail="Refresh already running")
        job.update(running=True, step=0, label="Starting", error=None, finished_at=None)
    background.add_task(run_pipeline)
    return {"started": True}


@app.get("/api/refresh/status", response_model=RefreshStatus)
def api_status():
    return {**job, "total_steps": len(PIPELINE)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

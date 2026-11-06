"""Web app for the Public Sentiment Analyzer (FastAPI).

Run:  python server.py   ->  http://127.0.0.1:8000   (API docs at /docs)
Uses the same reddit.db as the CLI. "Refresh" runs the same pipeline as CLI option 2.
"""
import os
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
os.chdir(BASE)  # the DB path is relative, so always work from the project folder

import web_report  # noqa: E402
from schemas import (DataSummary, RefreshOptions, RefreshStatus,  # noqa: E402
                     TopicReport, TopicSummary)

app = FastAPI(title="Public Sentiment Analyzer")

if (BASE / "static").is_dir():
    app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

# Same steps, same order as app.py option 2
PIPELINE = [
    ("reset_db.py", "Resetting DB"),
    ("fetch_rising.py", "Fetching posts"),
    ("fetch_comments.py", "Fetching comments"),
    ("extract_post_entities.py", "Extracting topic entities"),
    ("clear_entity_stance.py", "Clearing stance table"),
    ("analyze_entity_stance_auto.py", "Analyzing entity stance"),
    ("analyze_topic_stance.py", "Analyzing topic stance"),
]

job = {"running": False, "step": 0, "label": "", "detail": "", "error": None,
       "finished_at": None, "options": None}
lock = threading.Lock()


def run_pipeline(opts: RefreshOptions):
    """Runs in a worker thread so the site stays responsive during a refresh."""
    # config.py reads these, so every pipeline script sees the chosen settings
    env = {**os.environ, "PYTHONUNBUFFERED": "1",
           "PSA_POSTS": str(opts.posts), "PSA_SORT": opts.sort,
           "PSA_COMMENTS": str(opts.comments), "PSA_COMMENT_ORDER": opts.comment_order}
    try:
        for i, (script, label) in enumerate(PIPELINE, start=1):
            job.update(step=i, label=label, detail="")
            proc = subprocess.Popen([sys.executable, script], cwd=BASE, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            tail = deque(maxlen=5)
            for line in proc.stdout:  # stream output so the page can show live progress
                line = line.strip()
                if line:
                    tail.append(line)
                    job["detail"] = line[:160]
            if proc.wait() != 0:
                last = tail[-1] if tail else "no output"
                job["error"] = f"{label} failed ({script}): {last[:300]}"
                return
        web_report.save_refresh_options(opts.model_dump(), int(time.time()))
    except Exception as exc:  # noqa: BLE001
        job["error"] = str(exc)
    finally:
        job.update(running=False, finished_at=int(time.time()), detail="")


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


@app.get("/api/summary", response_model=DataSummary)
def api_summary():
    return web_report.data_summary()


@app.post("/api/refresh", status_code=202)
def api_refresh(background: BackgroundTasks, opts: RefreshOptions | None = None):
    opts = opts or RefreshOptions()
    with lock:
        if job["running"]:
            raise HTTPException(status_code=409, detail="Refresh already running")
        job.update(running=True, step=0, label="Starting", detail="", error=None,
                   finished_at=None, options=opts.model_dump())
    background.add_task(run_pipeline, opts)
    return {"started": True}


@app.get("/api/refresh/status", response_model=RefreshStatus)
def api_status():
    return {**job, "total_steps": len(PIPELINE)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

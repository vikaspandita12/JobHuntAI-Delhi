import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.database import Database
from app.matcher import JobMatcher
from app.cover_letter import CoverLetterGenerator
from app.notifier import EmailNotifier
from app.scheduler import JobScheduler, _scan_and_notify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

db = Database()
matcher = JobMatcher()
cover_gen = CoverLetterGenerator()
notifier = EmailNotifier()
scheduler = JobScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    scheduler.start()
    logger.info("JobHuntAI Delhi started")
    yield
    scheduler.stop()


app = FastAPI(
    title="JobHuntAI Delhi",
    description="Automated job discovery for Vikas Pandita & Diksha Koul — Delhi NCR relocation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "JobHuntAI Delhi"}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    html_path = Path("frontend/index.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content="<h1>JobHuntAI Delhi</h1><p>See /docs for API</p>")


@app.get("/jobs")
def list_jobs(
    profile: str = Query(None, description="vikas or diksha"),
    status:  str = Query(None, description="new / applied / skipped"),
    min_score: int = Query(0),
    limit: int = Query(100),
):
    v_min = int(os.getenv("VIKAS_MIN_SCORE",  "60")) if profile == "vikas"  else min_score
    d_min = int(os.getenv("DIKSHA_MIN_SCORE", "50")) if profile == "diksha" else min_score
    effective_min = v_min if profile == "vikas" else d_min if profile == "diksha" else min_score
    jobs = db.get_jobs(profile=profile, status=status, min_score=effective_min, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/jobs/{job_id}/apply")
def mark_applied(job_id: str):
    db.update_job_status(job_id, "applied")
    return {"message": "Marked as applied", "job_id": job_id}


@app.post("/jobs/{job_id}/skip")
def mark_skipped(job_id: str):
    db.update_job_status(job_id, "skipped")
    return {"message": "Marked as skipped", "job_id": job_id}


class NoteBody(BaseModel):
    notes: str


@app.post("/jobs/{job_id}/notes")
def add_notes(job_id: str, body: NoteBody):
    db.update_notes(job_id, body.notes)
    return {"message": "Notes saved"}


@app.get("/cover-letter/{job_id}/{profile}")
def generate_cover_letter(job_id: str, profile: str):
    if profile not in ("vikas", "diksha"):
        raise HTTPException(status_code=400, detail="profile must be 'vikas' or 'diksha'")
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    letter = cover_gen.generate(job, profile)
    return {"cover_letter": letter, "profile": profile, "job_title": job["title"]}


@app.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(_scan_and_notify)
    return {"message": "Scan started — runs in background"}


@app.post("/notify")
def send_digest_now():
    vikas_jobs  = db.get_jobs(profile="vikas",  status="new", min_score=int(os.getenv("VIKAS_MIN_SCORE",  "60")))
    diksha_jobs = db.get_jobs(profile="diksha", status="new", min_score=int(os.getenv("DIKSHA_MIN_SCORE", "50")))
    notifier.send_daily_digest(vikas_jobs, diksha_jobs)
    return {
        "message": "Digest sent",
        "vikas_jobs": len(vikas_jobs),
        "diksha_jobs": len(diksha_jobs),
    }


@app.get("/stats")
def get_stats():
    return db.get_stats()

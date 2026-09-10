"""Alpha-Sketch — upload an image, get an AI-narrated sketch video."""
import os
import shutil
import threading
import uuid

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .pipeline import run_pipeline

app = FastAPI(title="Alpha-Sketch")

JOBS = {}  # job_id -> {status, progress, stage, error, title, source, formats}
JOBS_LOCK = threading.Lock()
WORK = os.path.join(os.path.dirname(__file__), "..", "jobs")

ALLOWED = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _run_job(job_id: str, image_bytes: bytes, mime: str, lang: str):
    workdir = os.path.join(WORK, job_id)
    try:
        def cb(pct, stage):
            with JOBS_LOCK:
                JOBS[job_id]["progress"] = pct
                JOBS[job_id]["stage"] = stage
        result = run_pipeline(image_bytes, mime, lang, workdir, cb)
        with JOBS_LOCK:
            JOBS[job_id].update(
                status="done", progress=100, stage="Done",
                title=result["title"], source=result["source"],
                scenes=result["scenes"])
    except Exception as e:
        with JOBS_LOCK:
            JOBS[job_id].update(status="error", error=str(e))


@app.post("/api/generate")
async def generate(background: BackgroundTasks,
                   image: UploadFile = File(...),
                   lang: str = Form("en")):
    if image.content_type not in ALLOWED:
        raise HTTPException(400, "Image must be JPEG, PNG or WebP")
    data = await image.read()
    if len(data) > 12 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 12 MB)")
    if lang not in ("en", "ar", "ku"):
        lang = "en"
    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "running", "progress": 0,
                        "stage": "Queued", "error": None}
    background.add_task(_run_job, job_id, data, image.content_type, lang)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def status(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown job")
    return job


@app.get("/api/video/{job_id}/{fmt}")
def video(job_id: str, fmt: str):
    if fmt not in ("vertical", "landscape"):
        raise HTTPException(400, "fmt must be vertical or landscape")
    path = os.path.join(WORK, job_id, f"video_{fmt}.mp4")
    if not os.path.exists(path):
        raise HTTPException(404, "Video not ready")
    return FileResponse(path, media_type="video/mp4",
                        filename=f"alphasketch_{job_id}_{fmt}.mp4")


@app.get("/api/sketch/{job_id}/{style}")
def sketch_preview(job_id: str, style: str):
    if style not in ("pencil", "color", "cartoon", "blueprint"):
        raise HTTPException(400, "Unknown style")
    path = os.path.join(WORK, job_id, f"sketch_{style}.png")
    if not os.path.exists(path):
        raise HTTPException(404, "Not ready")
    return FileResponse(path, media_type="image/png")


app.mount("/", StaticFiles(directory="static", html=True), name="static")

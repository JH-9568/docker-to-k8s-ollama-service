import os, uuid, json, time
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RESULT_TTL = int(os.getenv("WORKER_RESULT_TTL", "3600"))
r = redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="Prompt_Service API", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

class RunRequest(BaseModel):
    prompt: str

@app.get("/health")
def health():
    try:
        r.ping()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run")
def run_task(req: RunRequest):
    job_id = str(uuid.uuid4())
    payload = {"job_id": job_id, "prompt": req.prompt, "ts": time.time()}
    r.lpush("prompthub:jobs", json.dumps(payload))
    r.setex(f"prompthub:status:{job_id}", RESULT_TTL, "queued")
    return {"job_id": job_id}

@app.get("/api/result/{job_id}")
def get_result(job_id: str):
    key = f"prompthub:result:{job_id}"
    data = r.get(key)
    if not data:
        status = r.get(f"prompthub:status:{job_id}")
        if status is None:
            raise HTTPException(status_code=404, detail="job_id not found")
        return {"job_id": job_id, "status": status}
    try:
        obj = json.loads(data)
    except Exception:
        obj = {"result": data}
    return {"job_id": job_id, "status": "done", "data": obj}

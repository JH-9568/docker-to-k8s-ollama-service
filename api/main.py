import os, uuid, json, time
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RESULT_TTL = int(os.getenv("WORKER_RESULT_TTL", "3600"))
r = redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="Prompt_Service API", version="3.0.0")

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
    # 히스토리 저장 최대 10개까지
    r.lpush("prompthub:history", json.dumps(payload))
    r.ltrim("prompthub:history", 0, 9)

    r.setex(f"prompthub:status:{job_id}", RESULT_TTL, "queued")
    return {"job_id": job_id}

# 히스토리 조회 api 
@app.get("/api/history")
def get_history():
    items = r.lrange("prompthub:history", 0, -1)
    history = []
    for i in items:
        try:
            obj = json.loads(i)
            jid = obj.get("job_id")
            if jid:
                res_raw = r.get(f"prompthub:result:{jid}")
                if res_raw:
                    try:
                        res_obj = json.loads(res_raw)
                    except Exception:
                        res_obj = {"output": res_raw}
                    # 주로 output 필드를 쓰고, 없으면 전체 객체를 전달
                    obj["result"] = res_obj.get("output") if isinstance(res_obj, dict) else res_obj
            history.append(obj)
        except:
            continue
    return history

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

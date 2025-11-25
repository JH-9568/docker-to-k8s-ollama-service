import os, json, time, sys, redis, requests, logging


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RESULT_TTL = int(os.getenv("WORKER_RESULT_TTL", "3600"))
PROVIDER = os.getenv("PROVIDER", "mock")            
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='[worker] %(asctime)s %(message)s'
)

r = redis.from_url(REDIS_URL, decode_responses=True)

def run_with_mock(prompt: str):
    return {"provider": "mock", "output": prompt, "tokens_est": len(prompt.split())}

def run_with_ollama(prompt: str):
    logging.info(f"ollama request model={OLLAMA_MODEL} len={len(prompt)}")
    res = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    res.raise_for_status()
    data = res.json()
    out = data.get("response", "")
    logging.info(f"ollama response bytes={len(out)}")
    return {"provider": "ollama", "output": out, "model": OLLAMA_MODEL}

def main():
    logging.info(f"starting… provider={PROVIDER} ollama={OLLAMA_URL} model={OLLAMA_MODEL}")
    while True:
        _, job = r.brpop("prompthub:jobs")
        logging.info(f"dequeued: {job}")
        job = json.loads(job)
        jid, prompt = job["job_id"], job["prompt"]
        try:
            r.setex(f"prompthub:status:{jid}", RESULT_TTL, "running")
            out = run_with_ollama(prompt) if PROVIDER == "ollama" else run_with_mock(prompt)
            r.setex(f"prompthub:result:{jid}", RESULT_TTL, json.dumps(out))
            r.setex(f"prompthub:status:{jid}", RESULT_TTL, "done")
            logging.info(f"done jid={jid} provider={out.get('provider')} bytes={len(out.get('output',''))}")
        except Exception as e:
            r.setex(f"prompthub:status:{jid}", RESULT_TTL, f"error: {e}")
            logging.exception(f"ERROR jid={jid}: {e}")
        time.sleep(0.01)

if __name__ == "__main__":
    main()

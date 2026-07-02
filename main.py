import time
import json
import uuid
from collections import deque
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()

EMAIL = "24f2007256@ds.study.iitm.ac.in"
START_TIME = time.time()

REQUEST_COUNTER = Counter("http_requests_total", "Total HTTP requests")

LOG_BUFFER = deque(maxlen=1000)


def add_log(level: str, path: str, request_id: str, extra: dict = None):
    entry = {
        "level": level,
        "ts": time.time(),
        "path": path,
        "request_id": request_id,
    }
    if extra:
        entry.update(extra)
    LOG_BUFFER.append(entry)


@app.middleware("http")
async def add_metrics_and_logs(request: Request, call_next):
    REQUEST_COUNTER.inc()
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    add_log("info", request.url.path, request_id)
    return response


@app.get("/work")
async def work(n: int = 1):
    total = 0
    for i in range(n):
        total += i
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
async def healthz():
    uptime = time.time() - START_TIME
    return {"status": "ok", "uptime_s": uptime}


@app.get("/logs/tail")
async def logs_tail(limit: int = 10):
    logs = list(LOG_BUFFER)[-limit:]
    return JSONResponse(content=logs)

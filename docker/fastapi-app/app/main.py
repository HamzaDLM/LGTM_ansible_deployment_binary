import json
import logging
import os
import random
import time
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import Redis


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": os.getenv("OTEL_SERVICE_NAME", "fastapi-demo"),
        }
        if hasattr(record, "extra"):
            payload.update(record.extra)
        return json.dumps(payload)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger("fastapi-demo")


def configure_tracing() -> None:
    provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "fastapi-demo")})
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(insecure=True)))
    trace.set_tracer_provider(provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    yield
    await app.state.redis.aclose()


configure_tracing()
RedisInstrumentor().instrument()

app = FastAPI(title="FastAPI LGTM demo", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.middleware("http")
async def access_log(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        "request completed",
        extra={
            "extra": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": elapsed_ms,
            }
        },
    )
    return response


@app.get("/")
async def root():
    return {"message": "FastAPI LGTM demo", "try": ["/health", "/slow", "/error", "/cache/example"]}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/slow")
async def slow():
    delay = random.uniform(0.2, 1.5)
    await asyncio.sleep(delay)
    return {"delay_seconds": round(delay, 3)}


@app.get("/error")
async def error():
    logger.error("intentional demo error")
    raise HTTPException(status_code=500, detail="intentional demo error")


@app.get("/cache/{key}")
async def cache_value(key: str, request: Request):
    redis: Redis = request.app.state.redis
    value = await redis.get(key)
    if value is None:
        value = f"value-{random.randint(1000, 9999)}"
        await redis.set(key, value, ex=60)
        return {"key": key, "value": value, "cache": "miss"}
    return {"key": key, "value": value, "cache": "hit"}

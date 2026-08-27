from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.certificates import router as certificates_router
from app.api.diagnostics import router as diagnostics_router
from app.api.kafka import router as kafka_router
from app.api.operations import router as operations_router
from app.api.postgres import router as postgres_router
from app.api.realtime import router as realtime_router
from app.api.routes import router
from app.api.s3 import router as s3_router
from app.api.victoriametrics import router as victoriametrics_router
from app.core.config import load_config
from app.core.db import init_db
from app.services.action_runner import action_catalog


templates = Jinja2Templates(directory="/app/app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="OpsDeck",
    description="Self-service operations portal for engineering teams",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(operations_router)
app.include_router(certificates_router)
app.include_router(victoriametrics_router)
app.include_router(kafka_router)
app.include_router(postgres_router)
app.include_router(s3_router)
app.include_router(diagnostics_router)
app.include_router(realtime_router)
app.mount("/static", StaticFiles(directory="/app/app/static"), name="static")


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": load_config(),
            "actions": action_catalog(),
        },
    )

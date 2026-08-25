from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.api.operations import router as operations_router
from app.core.db import init_db
from app.core.config import load_config

templates = Jinja2Templates(directory='/app/app/templates')

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title='OpsDeck', version='0.2.0', lifespan=lifespan)
app.include_router(router)
app.include_router(operations_router)
app.mount('/static', StaticFiles(directory='/app/app/static'), name='static')

@app.get('/healthz')
async def healthz():
    return {'status': 'ok'}

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request, 'config': load_config()})

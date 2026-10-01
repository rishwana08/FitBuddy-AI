from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered personalized fitness "
        "planning application."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


app.include_router(router)


@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "fitbuddy",
    }
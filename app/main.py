from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    web_directory = Path(__file__).parent / "web"
    application = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    application.mount("/static", StaticFiles(directory=web_directory), name="static")

    @application.get("/", include_in_schema=False)
    def web_app() -> FileResponse:
        return FileResponse(web_directory / "index.html")

    return application


app = create_app()

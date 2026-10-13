"""FastAPI assembly. Engine is chosen here — the single wiring point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import APP_VERSION
from app.api.routes import router
from app.config import Settings
from app.engine import build_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Qwen Offline Chat", version=APP_VERSION, docs_url=None, redoc_url=None)

    app.state.settings = settings
    app.state.engine = build_engine(settings)

    app.include_router(router)

    frontend = settings.frontend_dir
    if frontend.is_dir():
        # Mounted LAST so /v1/* and /api/* always win.
        app.mount("/", StaticFiles(directory=frontend, html=True), name="ui")
    return app


# Module-level instance for `uvicorn app.main:app`
app = create_app()

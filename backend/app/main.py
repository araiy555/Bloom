import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, datasets, projects
from app.core.config import get_settings
from app.db.session import Base, engine

settings = get_settings()


def create_app() -> FastAPI:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="Bloom API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(datasets.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    return app


app = create_app()

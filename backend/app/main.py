from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.database import init_db
from .dependencies.security import require_api_key
from .routes import assets, health, jobs, uploads, metrics

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


secure_dependency = Depends(require_api_key)


app.include_router(health.router)
app.include_router(uploads.router, prefix=settings.api_prefix, dependencies=[secure_dependency])
app.include_router(jobs.router, prefix=settings.api_prefix, dependencies=[secure_dependency])
app.include_router(assets.router, prefix=settings.api_prefix, dependencies=[secure_dependency])
app.include_router(metrics.router, dependencies=[secure_dependency])

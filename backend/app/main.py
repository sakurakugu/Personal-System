"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import async_session_factory, engine, Base
from app.core.redis import close_redis
from app.services.seed import seed_admin

# Import all models so Base.metadata is populated
import app.models  # noqa: F401

# ── Rate limiter ─────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev convenience – use Alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed admin
    async with async_session_factory() as session:
        await seed_admin(session)
    yield
    # Shutdown
    await engine.dispose()
    await close_redis()


app = FastAPI(
    title="Sakurakuguの小窝 API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiter middleware ──────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Include routers ──────────────────────────────────────
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.articles import router as articles_router
from app.api.v1.categories_tags import router as cat_tag_router
from app.api.v1.comments import router as comments_router
from app.api.v1.todos import router as todos_router
from app.api.v1.files import router as files_router
from app.api.v1.stats import router as stats_router
from app.api.v1.admin import router as admin_router

API_V1 = "/api/v1"
app.include_router(auth_router, prefix=API_V1)
app.include_router(users_router, prefix=API_V1)
app.include_router(articles_router, prefix=API_V1)
app.include_router(cat_tag_router, prefix=API_V1)
app.include_router(comments_router, prefix=API_V1)
app.include_router(todos_router, prefix=API_V1)
app.include_router(files_router, prefix=API_V1)
app.include_router(stats_router, prefix=API_V1)
app.include_router(admin_router, prefix=API_V1)


@app.get("/api/health")
async def health():
    return {"status": "ok"}

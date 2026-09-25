import sys
import asyncio

# Enable psycopg 3 async compatibility on Windows
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import (
    health,
    admin,
    sessions,
    cases,
    assessment,
    transcription,
    emotion,
    stress,
    multimodal,
    recommendations,
    svi,
    auth,
    responder,
    demo
)
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation: verify whether local Gemma runtime is reachable
    try:
        from app.services.llm.service import gemma_service
        is_ready, details = gemma_service.check_health()
        if is_ready:
            logger.info(
                f"[GEMMA] Local runtime reachable with provider={settings.GEMMA_PROVIDER} "
                f"model={settings.GEMMA_MODEL} runtime={settings.GEMMA_RUNTIME}"
            )
        else:
            logger.warning("[GEMMA ERROR] Local model unavailable")
    except Exception as e:
        logger.warning(f"[GEMMA ERROR] Local model unavailable: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Custom exception handler: Formats { "error": { ... } } for responder/auth endpoints
# while preserving { "detail": ... } for existing Phase 1-8 victim endpoints.
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    path = request.url.path
    if path.startswith(f"{settings.API_V1_STR}/auth") or path.startswith(f"{settings.API_V1_STR}/responder") or path.startswith(f"{settings.API_V1_STR}/admin") or path.startswith(f"{settings.API_V1_STR}/cases"):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail, headers=exc.headers)
        elif isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content={"error": exc.detail}, headers=exc.headers)
        else:
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
                headers=exc.headers
            )
    # Fallback to standard FastAPI error format for victim routes
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)

# CORS middleware for Web, Android emulator, and LAN devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root level health endpoint: GET /health
app.include_router(health.router)

# Versioned API routes under /api/v1
app.include_router(sessions.router, prefix=settings.API_V1_STR)
app.include_router(cases.router, prefix=settings.API_V1_STR)
app.include_router(assessment.router, prefix=settings.API_V1_STR)
app.include_router(transcription.router, prefix=settings.API_V1_STR)
app.include_router(emotion.router, prefix=settings.API_V1_STR)
app.include_router(stress.router, prefix=settings.API_V1_STR)
app.include_router(multimodal.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(svi.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(responder.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

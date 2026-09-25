from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.responses import JSONResponse
from app.db.session import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/health/db")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Database connectivity health check verifying connection to PostgreSQL 18 sih26093."""
    try:
        res = await db.execute(text("SELECT current_database();"))
        db_name = res.scalar_one_or_none()
        if db_name != "sih26093":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Connected to unexpected database: {db_name}"
            )
        return {
            "status": "ok",
            "database": db_name,
            "engine": "PostgreSQL 18",
            "driver": "SQLAlchemy 2.x + psycopg 3"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )

@router.get("/health/ai")
@router.get("/api/v1/health/ai")
async def ai_health_check():

    """AI health check verifying local Gemma 3 12B IT runtime connectivity."""
    from app.core.config import settings
    from app.services.llm.service import gemma_service
    
    is_ready = False
    details = {}
    try:
        is_ready, details = await gemma_service.check_health()
    except Exception as e:
        details = {"error": str(e)}
    
    status_str = "ready" if is_ready else "unavailable"
    payload = {
        "gemma": {
            "provider": settings.GEMMA_PROVIDER,
            "model": settings.GEMMA_MODEL,
            "runtime": settings.GEMMA_RUNTIME,
            "status": status_str,
        }
    }
    if details.get("models"):
        payload["gemma"]["available_models"] = details["models"]

    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload
        )
    return payload


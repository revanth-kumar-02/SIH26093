from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.db.session import get_db
from app.db.models.responder import Responder, UserRole
from app.db.models.audit import AuditEvent
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, ResponderRead, SupabaseAuthSyncRequest
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_responder
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate or retrieve token for user profile in development/testing.
    In production, Supabase Auth handles credentials and client issues Bearer tokens directly.
    """
    username_raw = credentials.username.strip()
    username_clean = username_raw.lower()
    stmt = select(Responder).where(
        or_(
            Responder.username == username_raw,
            Responder.username == username_clean,
            Responder.email == username_clean,
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid username/email or password."}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "ACCOUNT_DISABLED", "message": "Account has been deactivated."}},
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)

    # Append-only audit event for login
    audit_log = AuditEvent(
        case_id=None,
        actor_id=user.id,
        actor_type=user.role.value,
        event_type="USER_LOGIN",
        entity_type="AUTH",
        entity_id=user.id,
        event_metadata={"username": user.username, "role": user.role.value}
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        extra_claims={
            "display_name": user.display_name, 
            "username": user.username,
            "email": user.email
        }
    )
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role.value,
        responder_id=user.id,
        display_name=user.display_name
    )

@router.post("/sync", response_model=ResponderRead)
async def sync_supabase_session(
    sync_req: SupabaseAuthSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate a Supabase Auth JWT from the client and synchronize/return the PostgreSQL user profile.
    """
    payload = decode_token(sync_req.access_token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Missing subject UUID in Supabase token."}},
        )

    # Query PostgreSQL
    user = (await db.execute(select(Responder).where(Responder.id == str(user_id)))).scalars().first()
    if not user:
        email = payload.get("email") or f"user_{str(user_id)[:8]}@auth.local"
        username = email.split("@")[0]
        display_name = sync_req.display_name or payload.get("user_metadata", {}).get("display_name") or username
        role_raw = payload.get("app_metadata", {}).get("role") or payload.get("user_metadata", {}).get("role") or "PEOPLE"
        role_enum = UserRole.ADMIN if str(role_raw).upper() == "ADMIN" else UserRole.PEOPLE

        user = Responder(
            id=str(user_id),
            username=username,
            email=email,
            display_name=display_name,
            role=role_enum,
            is_active=True,
            last_login_at=datetime.now(timezone.utc)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

    return user

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Issue a fresh access token using a valid refresh token."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN_TYPE", "message": "Refresh token required."}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    stmt = select(Responder).where(Responder.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User inactive or not found."}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        extra_claims={
            "display_name": user.display_name, 
            "username": user.username,
            "email": user.email
        }
    )
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role.value,
        responder_id=user.id,
        display_name=user.display_name
    )

@router.get("/me", response_model=ResponderRead)
async def get_me(
    current_user: Responder = Depends(get_current_responder)
):
    """Retrieve profile and role information of current authenticated user from PostgreSQL."""
    return current_user


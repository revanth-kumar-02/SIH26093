from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.db.session import get_db
from app.db.models.responder import Responder, UserRole
from app.db.models.audit import AuditEvent
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, ResponderRead
from app.core.auth import (
    verify_password,
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
    """Authenticate a user (PEOPLE or ADMIN) and issue JWT tokens."""
    # Find user by username or email
    username_clean = credentials.username.strip().lower()
    conditions = [
        Responder.username == credentials.username.strip(),
        Responder.email == username_clean,
    ]
    if username_clean in ["admin@localhost", "admin@nhaa.gov.in", "admin_user", "admin"]:
        conditions.append(Responder.role == UserRole.ADMIN)
    elif username_clean in ["people@localhost", "people@nhaa.gov.in", "people_user", "people"]:
        conditions.append(Responder.role == UserRole.PEOPLE)

    stmt = select(Responder).where(or_(*conditions))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.password_hash):
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
        extra_claims={"display_name": user.display_name, "username": user.username}
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
        extra_claims={"display_name": user.display_name, "username": user.username}
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
    """Retrieve profile and role information of current authenticated user."""
    return current_user

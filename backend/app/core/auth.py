import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.config import settings
from app.db.session import get_db
from app.db.models.responder import Responder, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with automatic salt (utility helper)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash (utility helper)."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(
    subject: str,
    role: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token compatible with Supabase JWT structure."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    clean_role = role.upper() if role.upper() in ["ADMIN", "PEOPLE"] else "PEOPLE"
    
    payload = {
        "sub": subject,
        "aud": "authenticated",
        "role": "authenticated",
        "app_metadata": {
            "provider": "supabase",
            "role": clean_role,
        },
        "user_metadata": {
            "role": clean_role,
        },
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        if "role" in extra_claims:
            payload["role"] = extra_claims["role"]
            payload["user_metadata"]["role"] = extra_claims["role"]
            payload["app_metadata"]["role"] = extra_claims["role"]
        payload.update(extra_claims)
        
    secret = settings.SUPABASE_JWT_SECRET or settings.JWT_SECRET_KEY
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    secret = settings.SUPABASE_JWT_SECRET or settings.JWT_SECRET_KEY
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a Supabase / Application JWT token."""
    secrets_to_try = [
        settings.SUPABASE_JWT_SECRET,
        settings.JWT_SECRET_KEY,
    ]
    # Remove duplicate secrets
    secrets_to_try = list(dict.fromkeys([s for s in secrets_to_try if s]))

    last_err = None
    for secret in secrets_to_try:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM, "HS256"],
                options={"verify_aud": False}
            )
            return payload
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "TOKEN_EXPIRED", "message": "Authentication token has expired."}},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError as exc:
            last_err = exc

    # If none of the secrets worked:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "INVALID_TOKEN", "message": "Could not validate Supabase authentication credentials."}},
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_responder(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Responder:
    """
    FastAPI dependency to retrieve the authenticated identity from Supabase JWT
    and resolve/authorize the application profile in PostgreSQL.
    """
    payload = decode_token(token)
    token_type = payload.get("type")
    if token_type and token_type == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN_TYPE", "message": "Access token required."}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Supabase token missing subject identity."}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract role from metadata claims or direct role claim
    app_meta = payload.get("app_metadata", {})
    user_meta = payload.get("user_metadata", {})
    raw_role = (
        app_meta.get("role") or 
        user_meta.get("role") or 
        payload.get("role") or 
        "PEOPLE"
    )
    role_enum = UserRole.ADMIN if str(raw_role).upper() == "ADMIN" else UserRole.PEOPLE

    # Query PostgreSQL responders by UUID (sub)
    query = select(Responder).where(Responder.id == str(user_id))
    result = await db.execute(query)
    user = result.scalars().first()

    # If profile not found in PostgreSQL, auto-provision JIT profile
    if not user:
        email = payload.get("email") or user_meta.get("email") or f"user_{str(user_id)[:8]}@auth.local"
        username = user_meta.get("username") or payload.get("username") or email.split("@")[0]
        display_name = user_meta.get("display_name") or payload.get("display_name") or username

        # Ensure unique username
        existing_username = (await db.execute(
            select(Responder).where(Responder.username == username)
        )).scalars().first()
        if existing_username:
            username = f"{username}_{str(user_id)[:4]}"

        user = Responder(
            id=str(user_id),
            username=username,
            email=email,
            display_name=display_name,
            role=role_enum,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "USER_INACTIVE", "message": "User account is deactivated."}},
        )
        
    return user

def require_roles(allowed_roles: List[UserRole]):
    """Enforce strict role-based access control (RBAC). Only allowed roles pass."""
    async def role_checker(current_user: Responder = Depends(get_current_responder)) -> Responder:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": f"Role '{current_user.role.value}' is not authorized to access this administrative resource. Admin access required."
                    }
                }
            )
        return current_user
    return role_checker

def require_admin():
    """Dependency helper for administrative endpoints."""
    return require_roles([UserRole.ADMIN])

def require_people():
    """Dependency helper for people/victim endpoints."""
    return require_roles([UserRole.PEOPLE])


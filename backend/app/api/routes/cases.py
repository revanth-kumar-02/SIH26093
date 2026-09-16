import uuid
from datetime import datetime, timezone
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.responder import Responder, UserRole
from app.db.models.case import Case, CaseStatus
from app.db.models.conversation import Conversation
from app.db.models.audit import AuditEvent
from app.core.auth import get_current_responder, require_roles
from app.schemas.case import CaseListItem, CaseListResponse, CaseDetailResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["Cases & Sessions Management"])

class CaseCreateRequest(BaseModel):
    language: str = Field(default="en", description="Preferred interaction language")
    consent_status: str = Field(default="CONSENT_GIVEN", description="Consent confirmation")

class CaseResponse(BaseModel):
    id: str
    external_case_reference: str
    status: str
    language: str
    consent_status: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

class SessionItem(BaseModel):
    id: str
    session_id: str
    case_id: str
    status: str
    input_language: str
    started_at: datetime
    ended_at: Optional[datetime] = None

class SessionCreateRequest(BaseModel):
    language: str = Field(default="en", description="Session language")

@router.get("", response_model=List[CaseResponse])
async def list_cases(
    current_user: Responder = Depends(get_current_responder),
    db: AsyncSession = Depends(get_db)
):
    """List cases accessible by the current user.
    
    PEOPLE: Access ONLY their own cases.
    ADMIN: Access all triage cases.
    """
    if current_user.role == UserRole.ADMIN:
        stmt = select(Case).order_by(desc(Case.updated_at))
    else:
        stmt = select(Case).where(Case.user_id == current_user.id).order_by(desc(Case.updated_at))
    
    res = await db.execute(stmt)
    cases = res.scalars().all()
    return [
        CaseResponse(
            id=c.id,
            external_case_reference=c.external_case_reference,
            status=c.status.value,
            language=c.language,
            consent_status=c.consent_status,
            created_at=c.created_at,
            updated_at=c.updated_at,
            closed_at=c.closed_at
        ) for c in cases
    ]

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    request: CaseCreateRequest = CaseCreateRequest(),
    current_user: Responder = Depends(get_current_responder),
    db: AsyncSession = Depends(get_db)
):
    """Create a new case linked to the authenticated user."""
    case_ref = f"NHAA-2026-USR-{uuid.uuid4().hex[:8].upper()}"
    new_case = Case(
        external_case_reference=case_ref,
        status=CaseStatus.NEW,
        language=request.language,
        consent_status=request.consent_status,
        user_id=current_user.id
    )
    db.add(new_case)
    await db.flush()

    audit = AuditEvent(
        case_id=new_case.id,
        actor_id=current_user.id,
        actor_type=current_user.role.value,
        event_type="CASE_CREATED",
        entity_type="CASE",
        entity_id=new_case.id,
        event_metadata={"case_reference": case_ref, "language": request.language}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(new_case)

    return CaseResponse(
        id=new_case.id,
        external_case_reference=new_case.external_case_reference,
        status=new_case.status.value,
        language=new_case.language,
        consent_status=new_case.consent_status,
        created_at=new_case.created_at,
        updated_at=new_case.updated_at,
        closed_at=new_case.closed_at
    )

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    current_user: Responder = Depends(get_current_responder),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve case details with strict object-level access control."""
    stmt = select(Case).where(Case.id == case_id)
    res = await db.execute(stmt)
    case = res.scalars().first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found."}}
        )

    # Object-level authorization check:
    # PEOPLE can only view their own cases
    if current_user.role == UserRole.PEOPLE and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "You do not have access to this case."}}
        )

    return CaseResponse(
        id=case.id,
        external_case_reference=case.external_case_reference,
        status=case.status.value,
        language=case.language,
        consent_status=case.consent_status,
        created_at=case.created_at,
        updated_at=case.updated_at,
        closed_at=case.closed_at
    )

@router.get("/{case_id}/sessions", response_model=List[SessionItem])
async def get_case_sessions(
    case_id: str,
    current_user: Responder = Depends(get_current_responder),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all interaction sessions under a case with object-level authorization."""
    stmt = select(Case).where(Case.id == case_id)
    res = await db.execute(stmt)
    case = res.scalars().first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found."}}
        )

    if current_user.role == UserRole.PEOPLE and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "You do not have access to this case."}}
        )

    sessions_stmt = select(Conversation).where(Conversation.case_id == case_id).order_by(desc(Conversation.started_at))
    sessions_res = await db.execute(sessions_stmt)
    convs = sessions_res.scalars().all()

    return [
        SessionItem(
            id=s.id,
            session_id=s.session_id,
            case_id=s.case_id,
            status=s.status,
            input_language=s.input_language,
            started_at=s.started_at,
            ended_at=s.ended_at
        ) for s in convs
    ]

@router.post("/{case_id}/sessions", response_model=SessionItem, status_code=status.HTTP_201_CREATED)
async def create_case_session(
    case_id: str,
    request: SessionCreateRequest = SessionCreateRequest(),
    current_user: Responder = Depends(get_current_responder),
    db: AsyncSession = Depends(get_db)
):
    """Create a new session within an existing permitted case."""
    stmt = select(Case).where(Case.id == case_id)
    res = await db.execute(stmt)
    case = res.scalars().first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found."}}
        )

    if current_user.role == UserRole.PEOPLE and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "You do not have access to this case."}}
        )

    from app.core.security import generate_session_id
    new_session_id = generate_session_id()
    new_conv = Conversation(
        case_id=case.id,
        session_id=new_session_id,
        input_language=request.language,
        status="ACTIVE"
    )
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)

    return SessionItem(
        id=new_conv.id,
        session_id=new_conv.session_id,
        case_id=new_conv.case_id,
        status=new_conv.status,
        input_language=new_conv.input_language,
        started_at=new_conv.started_at,
        ended_at=new_conv.ended_at
    )

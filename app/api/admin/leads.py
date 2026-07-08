"""Admin endpoints for lead management."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.deps import AdminKey, LeadRepoDep

router = APIRouter(prefix="/admin", tags=["admin"])


class LeadOut(BaseModel):
    id: UUID
    name: str
    phone: str
    email: str | None
    pickup_city: str | None
    destination_city: str | None
    num_people: int | None
    budget_inr: int | None
    status: str
    assigned_to: str | None
    notes: str | None
    contacted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(new|contacted|qualified|converted|lost)$",
    )
    assigned_to: str | None = None
    notes: str | None = None


@router.get("/leads", response_model=list[LeadOut])
async def list_leads(
    key: AdminKey,
    lead_repo: LeadRepoDep,
    status: str | None = Query(default=None, description="Filter by status."),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List leads, optionally filtered by status."""
    leads = await lead_repo.list_by_status(status=status, limit=limit, offset=offset)
    return leads


@router.patch("/leads/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    key: AdminKey,
    lead_repo: LeadRepoDep,
):
    """Update a lead's status, assignment, or notes."""
    try:
        updated = await lead_repo.update_status(
            lead_id,
            status=payload.status,
            assigned_to=payload.assigned_to,
            notes=payload.notes,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated
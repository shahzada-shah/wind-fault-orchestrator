"""Turbine registry endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.db import SessionDep
from app.models import Turbine
from app.schemas import (
    TurbineCreate,
    TurbineListResponse,
    TurbineResponse,
    TurbineUpdate,
)

router = APIRouter(prefix="/turbines", tags=["turbines"])


@router.post("", response_model=TurbineResponse, status_code=201)
def create_turbine(turbine: TurbineCreate, session: SessionDep):
    """
    Register a new wind turbine.

    Args:
        turbine: Turbine data
        session: Database session

    Returns:
        Created turbine

    Raises:
        HTTPException: If turbine_id already exists
    """
    # Check if turbine_id already exists
    existing = session.exec(
        select(Turbine).where(Turbine.turbine_id == turbine.turbine_id)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Turbine with turbine_id '{turbine.turbine_id}' already exists",
        )

    db_turbine = Turbine.model_validate(turbine)
    session.add(db_turbine)
    session.commit()
    session.refresh(db_turbine)

    return db_turbine


@router.get("", response_model=TurbineListResponse)
def list_turbines(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    location: Optional[str] = Query(None, description="Filter by location"),
):
    """
    List all registered turbines with optional filters.

    Args:
        session: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        is_active: Filter by active status
        location: Filter by location

    Returns:
        List of turbines and total count
    """
    query = select(Turbine)

    # Apply filters
    if is_active is not None:
        query = query.where(Turbine.is_active == is_active)
    if location:
        query = query.where(Turbine.location.contains(location))

    # Get total count
    total = len(session.exec(query).all())

    # Apply pagination
    query = query.offset(skip).limit(limit)
    turbines = session.exec(query).all()

    return TurbineListResponse(turbines=turbines, total=total)


@router.get("/{turbine_id}", response_model=TurbineResponse)
def get_turbine(turbine_id: str, session: SessionDep):
    """
    Get details of a specific turbine.

    Args:
        turbine_id: Turbine identifier
        session: Database session

    Returns:
        Turbine details

    Raises:
        HTTPException: If turbine not found
    """
    turbine = session.exec(
        select(Turbine).where(Turbine.turbine_id == turbine_id)
    ).first()

    if not turbine:
        raise HTTPException(status_code=404, detail="Turbine not found")

    return turbine


@router.patch("/{turbine_id}", response_model=TurbineResponse)
def update_turbine(turbine_id: str, turbine_update: TurbineUpdate, session: SessionDep):
    """
    Update turbine information.

    Args:
        turbine_id: Turbine identifier
        turbine_update: Fields to update
        session: Database session

    Returns:
        Updated turbine

    Raises:
        HTTPException: If turbine not found
    """
    turbine = session.exec(
        select(Turbine).where(Turbine.turbine_id == turbine_id)
    ).first()

    if not turbine:
        raise HTTPException(status_code=404, detail="Turbine not found")

    # Update fields
    update_data = turbine_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(turbine, field, value)

    turbine.updated_at = datetime.utcnow()
    session.add(turbine)
    session.commit()
    session.refresh(turbine)

    return turbine


@router.delete("/{turbine_id}", status_code=204)
def delete_turbine(turbine_id: str, session: SessionDep):
    """
    Delete a turbine (soft delete by setting is_active=False).

    Args:
        turbine_id: Turbine identifier
        session: Database session

    Raises:
        HTTPException: If turbine not found
    """
    turbine = session.exec(
        select(Turbine).where(Turbine.turbine_id == turbine_id)
    ).first()

    if not turbine:
        raise HTTPException(status_code=404, detail="Turbine not found")

    turbine.is_active = False
    turbine.updated_at = datetime.utcnow()
    session.add(turbine)
    session.commit()

    return None


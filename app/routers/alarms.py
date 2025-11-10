"""Alarm ingestion endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.db import SessionDep
from app.models import Alarm, AlarmStatus, Turbine
from app.rules_engine import RulesEngine
from app.schemas import AlarmCreate, AlarmListResponse, AlarmResponse, AlarmUpdate

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.post("", response_model=AlarmResponse, status_code=201)
def ingest_alarm(alarm: AlarmCreate, session: SessionDep):
    """
    Ingest a new turbine alarm.

    This endpoint receives alarm data from turbines and automatically
    generates recommendations based on the rules engine.

    Args:
        alarm: Alarm data
        session: Database session

    Returns:
        Created alarm

    Raises:
        HTTPException: If turbine not found
    """
    # Find the turbine
    turbine = session.exec(
        select(Turbine).where(Turbine.turbine_id == alarm.turbine_id)
    ).first()

    if not turbine:
        raise HTTPException(
            status_code=404,
            detail=f"Turbine with turbine_id '{alarm.turbine_id}' not found",
        )

    # Create alarm
    alarm_data = alarm.model_dump(exclude={"turbine_id"})
    db_alarm = Alarm(**alarm_data, turbine_db_id=turbine.id)

    # Set occurred_at if not provided
    if not db_alarm.occurred_at:
        db_alarm.occurred_at = datetime.utcnow()

    session.add(db_alarm)
    session.commit()
    session.refresh(db_alarm)

    # Generate recommendation automatically using advanced rules engine
    from app.models import Recommendation

    recommendation_data = RulesEngine.generate_recommendation(db_alarm, session)
    if recommendation_data:
        db_recommendation = Recommendation(**recommendation_data)
        session.add(db_recommendation)
        session.commit()

        # Update turbine state based on action
        if db_recommendation.action:
            RulesEngine.update_turbine_state(
                turbine.id, db_recommendation.action, db_alarm, session
            )

    return db_alarm


@router.get("", response_model=AlarmListResponse)
def list_alarms(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    turbine_id: Optional[str] = Query(None, description="Filter by turbine ID"),
    status: Optional[AlarmStatus] = Query(None, description="Filter by status"),
    alarm_code: Optional[str] = Query(None, description="Filter by alarm code"),
):
    """
    List alarms with optional filters.

    Args:
        session: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        turbine_id: Filter by turbine ID
        status: Filter by alarm status
        alarm_code: Filter by alarm code

    Returns:
        List of alarms and total count
    """
    query = select(Alarm)

    # Apply filters
    if turbine_id:
        turbine = session.exec(
            select(Turbine).where(Turbine.turbine_id == turbine_id)
        ).first()
        if turbine:
            query = query.where(Alarm.turbine_db_id == turbine.id)

    if status:
        query = query.where(Alarm.status == status)

    if alarm_code:
        query = query.where(Alarm.alarm_code == alarm_code)

    # Order by most recent first
    query = query.order_by(Alarm.occurred_at.desc())

    # Get total count
    total = len(session.exec(query).all())

    # Apply pagination
    query = query.offset(skip).limit(limit)
    alarms = session.exec(query).all()

    return AlarmListResponse(alarms=alarms, total=total)


@router.get("/{alarm_id}", response_model=AlarmResponse)
def get_alarm(alarm_id: int, session: SessionDep):
    """
    Get details of a specific alarm.

    Args:
        alarm_id: Alarm ID
        session: Database session

    Returns:
        Alarm details

    Raises:
        HTTPException: If alarm not found
    """
    alarm = session.get(Alarm, alarm_id)

    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    return alarm


@router.patch("/{alarm_id}", response_model=AlarmResponse)
def update_alarm(alarm_id: int, alarm_update: AlarmUpdate, session: SessionDep):
    """
    Update alarm status.

    Args:
        alarm_id: Alarm ID
        alarm_update: Fields to update
        session: Database session

    Returns:
        Updated alarm

    Raises:
        HTTPException: If alarm not found
    """
    alarm = session.get(Alarm, alarm_id)

    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    # Update fields
    update_data = alarm_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alarm, field, value)

    alarm.updated_at = datetime.utcnow()
    session.add(alarm)
    session.commit()
    session.refresh(alarm)

    return alarm


@router.post("/{alarm_id}/acknowledge", response_model=AlarmResponse)
def acknowledge_alarm(alarm_id: int, session: SessionDep):
    """
    Acknowledge an alarm.

    Args:
        alarm_id: Alarm ID
        session: Database session

    Returns:
        Updated alarm

    Raises:
        HTTPException: If alarm not found
    """
    alarm = session.get(Alarm, alarm_id)

    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    alarm.status = AlarmStatus.ACKNOWLEDGED
    alarm.acknowledged_at = datetime.utcnow()
    alarm.updated_at = datetime.utcnow()

    session.add(alarm)
    session.commit()
    session.refresh(alarm)

    return alarm


@router.post("/{alarm_id}/resolve", response_model=AlarmResponse)
def resolve_alarm(alarm_id: int, session: SessionDep):
    """
    Resolve an alarm.

    Args:
        alarm_id: Alarm ID
        session: Database session

    Returns:
        Updated alarm

    Raises:
        HTTPException: If alarm not found
    """
    alarm = session.get(Alarm, alarm_id)

    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    alarm.status = AlarmStatus.RESOLVED
    alarm.resolved_at = datetime.utcnow()
    alarm.updated_at = datetime.utcnow()

    session.add(alarm)
    session.commit()
    session.refresh(alarm)

    return alarm


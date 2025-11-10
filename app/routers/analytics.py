"""Analytics endpoints for fault analysis and trending."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import func, select

from app.db import SessionDep
from app.models import Alarm, Recommendation, Turbine

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============= Response Schemas =============


class FaultCodeStats(BaseModel):
    """Statistics for a fault code."""

    alarm_code: str
    count: int
    description: Optional[str] = None


class FaultFrequency(BaseModel):
    """Fault frequency statistics."""

    alarm_code: str
    count: int
    days: int
    frequency_per_day: float


class TroubledTurbine(BaseModel):
    """Turbine with most alarms."""

    turbine_id: str
    turbine_name: str
    alarm_count: int
    active_alarm_count: int
    location: str


class TemperatureTrend(BaseModel):
    """Temperature trend data point."""

    occurred_at: datetime
    temperature_c: float
    alarm_code: str


class AnalyticsSummary(BaseModel):
    """Overall analytics summary."""

    total_turbines: int
    active_turbines: int
    total_alarms: int
    active_alarms: int
    critical_alarms: int
    avg_temperature: Optional[float] = None


# ============= Analytics Endpoints =============


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(session: SessionDep):
    """
    Get overall analytics summary.

    Args:
        session: Database session

    Returns:
        Analytics summary with key metrics
    """
    # Count turbines
    total_turbines = len(session.exec(select(Turbine)).all())
    active_turbines = len(
        session.exec(select(Turbine).where(Turbine.is_active == True)).all()
    )

    # Count alarms
    total_alarms = len(session.exec(select(Alarm)).all())
    active_alarms = len(
        session.exec(select(Alarm).where(Alarm.status == "active")).all()
    )
    critical_alarms = len(
        session.exec(select(Alarm).where(Alarm.severity == "critical")).all()
    )

    # Calculate average temperature
    query = select(func.avg(Alarm.temperature_c)).where(
        Alarm.temperature_c.is_not(None)
    )
    avg_temp = session.exec(query).first()

    return AnalyticsSummary(
        total_turbines=total_turbines,
        active_turbines=active_turbines,
        total_alarms=total_alarms,
        active_alarms=active_alarms,
        critical_alarms=critical_alarms,
        avg_temperature=float(avg_temp) if avg_temp else None,
    )


@router.get("/top-faults", response_model=list[FaultCodeStats])
def get_top_faults(
    session: SessionDep,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    days: Optional[int] = Query(
        None, ge=1, le=365, description="Filter by last N days"
    ),
):
    """
    Get top fault codes by frequency.

    Args:
        session: Database session
        limit: Maximum number of results
        days: Optional filter for last N days

    Returns:
        List of fault codes with counts
    """
    query = select(Alarm.alarm_code, func.count(Alarm.id).label("count"))

    # Apply time filter if specified
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(Alarm.occurred_at >= cutoff_date)

    query = query.group_by(Alarm.alarm_code).order_by(func.count(Alarm.id).desc())

    # Execute query
    results = session.exec(query.limit(limit)).all()

    # Format response
    fault_stats = []
    for alarm_code, count in results:
        # Get a sample description
        sample_alarm = session.exec(
            select(Alarm).where(Alarm.alarm_code == alarm_code).limit(1)
        ).first()

        fault_stats.append(
            FaultCodeStats(
                alarm_code=alarm_code,
                count=count,
                description=sample_alarm.alarm_description if sample_alarm else None,
            )
        )

    return fault_stats


@router.get("/fault-frequency", response_model=FaultFrequency)
def get_fault_frequency(
    session: SessionDep,
    alarm_code: str = Query(..., description="Alarm code to analyze"),
    days: int = Query(7, ge=1, le=365, description="Time window in days"),
    turbine_id: Optional[str] = Query(
        None, description="Filter by specific turbine"
    ),
):
    """
    Get frequency statistics for a specific fault code.

    Args:
        session: Database session
        alarm_code: Alarm code to analyze
        days: Time window in days
        turbine_id: Optional turbine filter

    Returns:
        Fault frequency statistics
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Build query
    query = select(Alarm).where(
        Alarm.alarm_code == alarm_code, Alarm.occurred_at >= cutoff_date
    )

    # Apply turbine filter if specified
    if turbine_id:
        turbine = session.exec(
            select(Turbine).where(Turbine.turbine_id == turbine_id)
        ).first()
        if turbine:
            query = query.where(Alarm.turbine_db_id == turbine.id)

    # Count occurrences
    alarms = session.exec(query).all()
    count = len(alarms)

    return FaultFrequency(
        alarm_code=alarm_code,
        count=count,
        days=days,
        frequency_per_day=round(count / days, 2) if days > 0 else 0.0,
    )


@router.get("/turbines/troubled", response_model=list[TroubledTurbine])
def get_troubled_turbines(
    session: SessionDep,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    days: Optional[int] = Query(
        None, ge=1, le=365, description="Filter by last N days"
    ),
):
    """
    Get turbines with the most alarms (troubled turbines).

    Args:
        session: Database session
        limit: Maximum number of results
        days: Optional filter for last N days

    Returns:
        List of troubled turbines with alarm counts
    """
    # Build base query
    query = select(
        Turbine.turbine_id,
        Turbine.name,
        Turbine.location,
        func.count(Alarm.id).label("alarm_count"),
    ).join(Alarm, Turbine.id == Alarm.turbine_db_id)

    # Apply time filter if specified
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(Alarm.occurred_at >= cutoff_date)

    # Group and order
    query = (
        query.group_by(Turbine.turbine_id, Turbine.name, Turbine.location)
        .order_by(func.count(Alarm.id).desc())
        .limit(limit)
    )

    results = session.exec(query).all()

    # Format response with active alarm counts
    troubled = []
    for turbine_id, name, location, alarm_count in results:
        # Get turbine
        turbine = session.exec(
            select(Turbine).where(Turbine.turbine_id == turbine_id)
        ).first()

        if turbine:
            # Count active alarms
            active_count = len(
                session.exec(
                    select(Alarm).where(
                        Alarm.turbine_db_id == turbine.id, Alarm.status == "active"
                    )
                ).all()
            )

            troubled.append(
                TroubledTurbine(
                    turbine_id=turbine_id,
                    turbine_name=name,
                    alarm_count=alarm_count,
                    active_alarm_count=active_count,
                    location=location,
                )
            )

    return troubled


@router.get("/temp-trends/{turbine_id}", response_model=list[TemperatureTrend])
def get_temperature_trends(
    turbine_id: int,
    session: SessionDep,
    days: int = Query(7, ge=1, le=365, description="Time window in days"),
    alarm_code: Optional[str] = Query(
        None, description="Filter by specific alarm code"
    ),
):
    """
    Get temperature trends for a specific turbine.

    Args:
        turbine_id: Turbine database ID
        session: Database session
        days: Time window in days
        alarm_code: Optional alarm code filter

    Returns:
        List of temperature trend data points
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Build query
    query = (
        select(Alarm)
        .where(
            Alarm.turbine_db_id == turbine_id,
            Alarm.temperature_c.is_not(None),
            Alarm.occurred_at >= cutoff_date,
        )
        .order_by(Alarm.occurred_at.asc())
    )

    # Apply alarm code filter if specified
    if alarm_code:
        query = query.where(Alarm.alarm_code == alarm_code)

    alarms = session.exec(query).all()

    # Format response
    trends = [
        TemperatureTrend(
            occurred_at=alarm.occurred_at,
            temperature_c=alarm.temperature_c,
            alarm_code=alarm.alarm_code,
        )
        for alarm in alarms
    ]

    return trends


@router.get("/action-distribution")
def get_action_distribution(
    session: SessionDep,
    days: Optional[int] = Query(
        None, ge=1, le=365, description="Filter by last N days"
    ),
):
    """
    Get distribution of recommendation actions.

    Args:
        session: Database session
        days: Optional filter for last N days

    Returns:
        Distribution of actions with counts
    """
    query = select(
        Recommendation.action, func.count(Recommendation.id).label("count")
    ).where(Recommendation.action.is_not(None))

    # Apply time filter if specified
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(Recommendation.created_at >= cutoff_date)

    query = query.group_by(Recommendation.action)

    results = session.exec(query).all()

    # Format response
    distribution = {str(action): count for action, count in results}

    return {
        "distribution": distribution,
        "total": sum(distribution.values()),
        "days": days,
    }


@router.get("/escalation-rate")
def get_escalation_rate(
    session: SessionDep,
    days: int = Query(30, ge=1, le=365, description="Time window in days"),
):
    """
    Get escalation rate (percentage of alarms that were escalated).

    Args:
        session: Database session
        days: Time window in days

    Returns:
        Escalation rate statistics
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Total recommendations
    total_query = select(func.count(Recommendation.id)).where(
        Recommendation.created_at >= cutoff_date
    )
    total = session.exec(total_query).first() or 0

    # Escalated recommendations
    escalated_query = select(func.count(Recommendation.id)).where(
        Recommendation.created_at >= cutoff_date, Recommendation.action == "escalate"
    )
    escalated = session.exec(escalated_query).first() or 0

    # Calculate rate
    escalation_rate = (escalated / total * 100) if total > 0 else 0.0

    return {
        "total_recommendations": total,
        "escalated": escalated,
        "escalation_rate": round(escalation_rate, 2),
        "days": days,
    }


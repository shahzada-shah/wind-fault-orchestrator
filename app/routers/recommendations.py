"""Recommendation endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.db import SessionDep
from app.models import Alarm, Recommendation, RecommendationPriority
from app.rules_engine import RulesEngine
from app.schemas import (
    RecommendationCreate,
    RecommendationListResponse,
    RecommendationResponse,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationListResponse)
def list_recommendations(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    priority: Optional[RecommendationPriority] = Query(
        None, description="Filter by priority"
    ),
    is_automated: Optional[bool] = Query(None, description="Filter by automated flag"),
):
    """
    List all recommendations with optional filters.

    Args:
        session: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        priority: Filter by priority
        is_automated: Filter by automated flag

    Returns:
        List of recommendations and total count
    """
    query = select(Recommendation)

    # Apply filters
    if priority:
        query = query.where(Recommendation.priority == priority)

    if is_automated is not None:
        query = query.where(Recommendation.is_automated == is_automated)

    # Order by priority (urgent first) and creation time
    priority_order = {
        RecommendationPriority.URGENT: 0,
        RecommendationPriority.HIGH: 1,
        RecommendationPriority.MEDIUM: 2,
        RecommendationPriority.LOW: 3,
    }

    # Get all and sort in Python (SQLModel limitation for enum ordering)
    all_recommendations = session.exec(query).all()
    sorted_recommendations = sorted(
        all_recommendations,
        key=lambda r: (priority_order.get(r.priority, 99), -r.created_at.timestamp()),
    )

    # Apply pagination
    total = len(sorted_recommendations)
    recommendations = sorted_recommendations[skip : skip + limit]

    return RecommendationListResponse(recommendations=recommendations, total=total)


@router.get("/{alarm_id}", response_model=RecommendationListResponse)
def get_recommendations_for_alarm(alarm_id: int, session: SessionDep):
    """
    Get all recommendations for a specific alarm.

    Args:
        alarm_id: Alarm ID
        session: Database session

    Returns:
        List of recommendations for the alarm

    Raises:
        HTTPException: If alarm not found
    """
    # Verify alarm exists
    alarm = session.get(Alarm, alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    # Get recommendations
    query = select(Recommendation).where(Recommendation.alarm_db_id == alarm_id)
    recommendations = session.exec(query).all()

    return RecommendationListResponse(
        recommendations=recommendations, total=len(recommendations)
    )


@router.post("/{alarm_id}/generate", response_model=RecommendationResponse)
def generate_recommendation_for_alarm(alarm_id: int, session: SessionDep):
    """
    Generate a new recommendation for an alarm using the rules engine.

    Args:
        alarm_id: Alarm ID
        session: Database session

    Returns:
        Generated recommendation

    Raises:
        HTTPException: If alarm not found
    """
    # Get alarm
    alarm = session.get(Alarm, alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    # Generate recommendation
    recommendation_data = RulesEngine.generate_recommendation(alarm)
    if not recommendation_data:
        raise HTTPException(
            status_code=500, detail="Failed to generate recommendation"
        )

    # Create and save recommendation
    db_recommendation = Recommendation(**recommendation_data)
    session.add(db_recommendation)
    session.commit()
    session.refresh(db_recommendation)

    return db_recommendation


@router.post("", response_model=RecommendationResponse, status_code=201)
def create_manual_recommendation(
    recommendation: RecommendationCreate, session: SessionDep
):
    """
    Create a manual recommendation for an alarm.

    Args:
        recommendation: Recommendation data
        session: Database session

    Returns:
        Created recommendation

    Raises:
        HTTPException: If alarm not found
    """
    # Verify alarm exists
    alarm = session.get(Alarm, recommendation.alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    # Create recommendation
    recommendation_data = recommendation.model_dump(exclude={"alarm_id"})
    db_recommendation = Recommendation(
        **recommendation_data, alarm_db_id=recommendation.alarm_id, is_automated=False
    )

    session.add(db_recommendation)
    session.commit()
    session.refresh(db_recommendation)

    return db_recommendation


@router.get("/recommendation/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation(recommendation_id: int, session: SessionDep):
    """
    Get details of a specific recommendation.

    Args:
        recommendation_id: Recommendation ID
        session: Database session

    Returns:
        Recommendation details

    Raises:
        HTTPException: If recommendation not found
    """
    recommendation = session.get(Recommendation, recommendation_id)

    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return recommendation


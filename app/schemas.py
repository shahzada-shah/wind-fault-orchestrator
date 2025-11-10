"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import (
    AlarmSeverity,
    AlarmStatus,
    RecommendationAction,
    RecommendationPriority,
)


# ============= Turbine Schemas =============


class TurbineBase(BaseModel):
    """Base turbine schema."""

    turbine_id: str = Field(..., max_length=100, description="Unique turbine identifier")
    name: str = Field(..., max_length=200, description="Turbine name")
    location: str = Field(..., max_length=200, description="Physical location")
    model: str = Field(..., max_length=100, description="Turbine model")
    capacity_kw: float = Field(..., gt=0, description="Capacity in kilowatts")
    installation_date: Optional[datetime] = None
    is_active: bool = True
    state: str = Field(default="Online", description="Turbine state")


class TurbineCreate(TurbineBase):
    """Schema for creating a turbine."""

    pass


class TurbineUpdate(BaseModel):
    """Schema for updating a turbine."""

    name: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class TurbineResponse(TurbineBase):
    """Schema for turbine response."""

    id: int
    last_state_change: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Alarm Schemas =============


class AlarmBase(BaseModel):
    """Base alarm schema."""

    alarm_code: str = Field(..., max_length=50, description="Alarm code")
    alarm_description: str = Field(..., max_length=500, description="Alarm description")
    severity: AlarmSeverity = AlarmSeverity.MEDIUM
    occurred_at: Optional[datetime] = None
    resettable: bool = True
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    note: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    extra_metadata: Optional[str] = Field(None, description="Additional metadata as JSON string")


class AlarmCreate(AlarmBase):
    """Schema for creating an alarm."""

    turbine_id: str = Field(..., description="Turbine identifier")


class AlarmUpdate(BaseModel):
    """Schema for updating an alarm."""

    status: Optional[AlarmStatus] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlarmResponse(AlarmBase):
    """Schema for alarm response."""

    id: int
    turbine_db_id: int
    status: AlarmStatus
    resettable: bool
    temperature_c: Optional[float] = None
    note: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlarmWithTurbine(AlarmResponse):
    """Schema for alarm with turbine details."""

    turbine: TurbineResponse


# ============= Recommendation Schemas =============


class RecommendationBase(BaseModel):
    """Base recommendation schema."""

    title: str = Field(..., max_length=200, description="Recommendation title")
    description: str = Field(..., max_length=1000, description="Detailed description")
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    action: Optional[RecommendationAction] = Field(None, description="Recommended action")
    rationale: Optional[str] = Field(None, max_length=1000, description="Action rationale")
    snooze_until: Optional[datetime] = Field(None, description="Snooze until timestamp")
    action_items: Optional[str] = Field(None, description="Action items as JSON string")
    estimated_downtime_hours: Optional[float] = Field(None, ge=0)
    is_automated: bool = False


class RecommendationCreate(RecommendationBase):
    """Schema for creating a recommendation."""

    alarm_id: int


class RecommendationResponse(RecommendationBase):
    """Schema for recommendation response."""

    id: int
    alarm_db_id: int
    action: Optional[RecommendationAction] = None
    rationale: Optional[str] = None
    snooze_until: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationWithAlarm(RecommendationResponse):
    """Schema for recommendation with alarm details."""

    alarm: AlarmResponse


# ============= List Response Schemas =============


class TurbineListResponse(BaseModel):
    """Schema for list of turbines."""

    turbines: list[TurbineResponse]
    total: int


class AlarmListResponse(BaseModel):
    """Schema for list of alarms."""

    alarms: list[AlarmResponse]
    total: int


class RecommendationListResponse(BaseModel):
    """Schema for list of recommendations."""

    recommendations: list[RecommendationResponse]
    total: int


# ============= Health Check Schema =============


class HealthCheck(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str


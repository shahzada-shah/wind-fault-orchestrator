"""SQLModel database models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class AlarmSeverity(str, Enum):
    """Alarm severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlarmStatus(str, Enum):
    """Alarm status."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class RecommendationAction(str, Enum):
    """Recommendation action types."""

    RESET = "reset"
    ESCALATE = "escalate"
    WAIT_COOL_DOWN = "wait_cool_down"
    SNOOZE = "snooze"
    MANUAL_INSPECTION = "manual_inspection"


class RecommendationPriority(str, Enum):
    """Recommendation priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Turbine(SQLModel, table=True):
    """Wind turbine model."""

    __tablename__ = "turbines"

    id: Optional[int] = Field(default=None, primary_key=True)
    turbine_id: str = Field(unique=True, index=True, max_length=100)
    name: str = Field(max_length=200)
    location: str = Field(max_length=200)
    model: str = Field(max_length=100)
    capacity_kw: float
    installation_date: Optional[datetime] = None
    is_active: bool = Field(default=True)
    state: str = Field(default="Online", max_length=50)  # Online, Stopped, Faulted, Cooling
    last_state_change: Optional[datetime] = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    alarms: list["Alarm"] = Relationship(back_populates="turbine")


class Alarm(SQLModel, table=True):
    """Turbine alarm model (also known as FaultEvent)."""

    __tablename__ = "alarms"

    id: Optional[int] = Field(default=None, primary_key=True)
    turbine_db_id: int = Field(foreign_key="turbines.id")
    alarm_code: str = Field(index=True, max_length=50)
    alarm_description: str = Field(max_length=500)
    severity: AlarmSeverity = Field(default=AlarmSeverity.MEDIUM)
    status: AlarmStatus = Field(default=AlarmStatus.ACTIVE, index=True)
    occurred_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Enhanced fields for FHP-style logic
    resettable: bool = Field(default=True)
    temperature_c: Optional[float] = None
    note: Optional[str] = Field(default=None, max_length=1000)
    
    metadata: Optional[str] = None  # JSON string for additional data
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    turbine: Turbine = Relationship(back_populates="alarms")
    recommendations: list["Recommendation"] = Relationship(back_populates="alarm")


class Recommendation(SQLModel, table=True):
    """Alarm recommendation model."""

    __tablename__ = "recommendations"

    id: Optional[int] = Field(default=None, primary_key=True)
    alarm_db_id: int = Field(foreign_key="alarms.id")
    title: str = Field(max_length=200)
    description: str = Field(max_length=1000)
    priority: RecommendationPriority = Field(default=RecommendationPriority.MEDIUM)
    
    # Enhanced fields for FHP-style logic
    action: Optional[RecommendationAction] = Field(default=None)
    rationale: Optional[str] = Field(default=None, max_length=1000)
    snooze_until: Optional[datetime] = None  # For snoozed recommendations
    
    action_items: Optional[str] = None  # JSON string for action items list
    estimated_downtime_hours: Optional[float] = None
    is_automated: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    alarm: Alarm = Relationship(back_populates="recommendations")


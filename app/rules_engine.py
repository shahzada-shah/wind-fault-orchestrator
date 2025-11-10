"""Enhanced rules engine for generating recommendations based on alarms with FHP-style logic."""

import json
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlmodel import Session, select

from app.models import (
    Alarm,
    AlarmSeverity,
    Recommendation,
    RecommendationAction,
    RecommendationPriority,
)


class RulesEngine:
    """Business logic for analyzing alarms and generating recommendations with advanced FHP-style rules."""

    # Temperature threshold for cool-down action
    TEMP_THRESHOLD = 75.0

    # High-temperature alarm codes
    TEMP_CRITICAL_CODES = ["EM_83", "TEMP_HIGH", "GEARBOX_OVERHEAT", "GEARBOX_TEMP_HIGH"]

    # Frequency thresholds
    FREQ_24H_THRESHOLD = 4  # If alarm occurs 4+ times in 24h, escalate
    FREQ_7D_THRESHOLD = 8  # If alarm occurs 8+ times in 7d, escalate

    # Oscillation detection window (minutes)
    OSCILLATION_WINDOW = 10

    # Snooze default duration (minutes)
    DEFAULT_SNOOZE_MINUTES = 20

    # Define alarm code to recommendation mapping
    ALARM_RULES = {
        "GEARBOX_TEMP_HIGH": {
            "title": "Gearbox Temperature Critical",
            "description": "Gearbox temperature exceeds safe operating limits. Immediate inspection required.",
            "priority": RecommendationPriority.URGENT,
            "action_items": [
                "Reduce turbine load immediately",
                "Schedule emergency maintenance inspection",
                "Check lubrication system",
                "Monitor temperature every 15 minutes",
            ],
            "estimated_downtime_hours": 4.0,
        },
        "GENERATOR_VIBRATION": {
            "title": "Generator Vibration Detected",
            "description": "Abnormal vibration patterns detected in generator. May indicate bearing issues.",
            "priority": RecommendationPriority.HIGH,
            "action_items": [
                "Schedule vibration analysis",
                "Inspect generator bearings",
                "Check alignment",
                "Review maintenance logs",
            ],
            "estimated_downtime_hours": 8.0,
        },
        "PITCH_SYSTEM_FAULT": {
            "title": "Pitch System Malfunction",
            "description": "Blade pitch control system is not responding correctly.",
            "priority": RecommendationPriority.HIGH,
            "action_items": [
                "Stop turbine operation",
                "Inspect pitch motors and drives",
                "Check hydraulic system pressure",
                "Test backup pitch system",
            ],
            "estimated_downtime_hours": 12.0,
        },
        "YAW_ERROR": {
            "title": "Yaw System Error",
            "description": "Yaw system unable to align turbine with wind direction.",
            "priority": RecommendationPriority.MEDIUM,
            "action_items": [
                "Inspect yaw motors",
                "Check yaw brake system",
                "Calibrate wind direction sensors",
                "Verify control system signals",
            ],
            "estimated_downtime_hours": 6.0,
        },
        "GRID_DISCONNECT": {
            "title": "Grid Connection Lost",
            "description": "Turbine disconnected from power grid.",
            "priority": RecommendationPriority.URGENT,
            "action_items": [
                "Check grid voltage and frequency",
                "Inspect circuit breakers",
                "Verify protection relay settings",
                "Contact grid operator",
            ],
            "estimated_downtime_hours": 2.0,
        },
        "LOW_WIND_SPEED": {
            "title": "Low Wind Speed",
            "description": "Wind speed below cut-in threshold.",
            "priority": RecommendationPriority.LOW,
            "action_items": [
                "Monitor wind conditions",
                "Verify anemometer readings",
                "Check for ice buildup on blades",
            ],
            "estimated_downtime_hours": 0.0,
        },
        "EM_83": {
            "title": "EM-83 Fault Code",
            "description": "Critical system fault detected.",
            "priority": RecommendationPriority.URGENT,
            "action_items": [
                "Immediate system inspection required",
                "Check system diagnostics",
                "Review fault logs",
            ],
            "estimated_downtime_hours": 4.0,
        },
    }

    @classmethod
    def decide_action(
        cls, alarm: Alarm, session: Session
    ) -> Tuple[RecommendationAction, str]:
        """
        Decide the action to take based on FHP-style rules.

        Logic:
        1. If not resettable → Escalate
        2. Check oscillation (same code within 10 min) → Escalate
        3. Check frequency (≥4 in 24h or ≥8 in 7d) → Escalate
        4. If temperature >75°C for temp-critical codes → WaitCoolDown
        5. Else → Reset

        Args:
            alarm: The alarm to analyze
            session: Database session for querying history

        Returns:
            Tuple of (action, rationale)
        """
        # Rule 1: Not resettable → Escalate
        if not alarm.resettable:
            return (
                RecommendationAction.ESCALATE,
                "Alarm is not resettable and requires manual intervention.",
            )

        # Rule 2: Oscillation detection
        oscillation_detected = cls._check_oscillation(alarm, session)
        if oscillation_detected:
            return (
                RecommendationAction.ESCALATE,
                f"Oscillation detected: Same fault code appeared twice within {cls.OSCILLATION_WINDOW} minutes.",
            )

        # Rule 3: Frequency check
        freq_24h = cls._count_alarms_in_window(alarm, session, hours=24)
        freq_7d = cls._count_alarms_in_window(alarm, session, hours=168)  # 7 days

        if freq_24h >= cls.FREQ_24H_THRESHOLD:
            return (
                RecommendationAction.ESCALATE,
                f"High frequency: {freq_24h} occurrences in last 24 hours (threshold: {cls.FREQ_24H_THRESHOLD}).",
            )

        if freq_7d >= cls.FREQ_7D_THRESHOLD:
            return (
                RecommendationAction.ESCALATE,
                f"High frequency: {freq_7d} occurrences in last 7 days (threshold: {cls.FREQ_7D_THRESHOLD}).",
            )

        # Rule 4: Temperature check for critical codes
        if (
            alarm.alarm_code in cls.TEMP_CRITICAL_CODES
            and alarm.temperature_c is not None
            and alarm.temperature_c > cls.TEMP_THRESHOLD
        ):
            return (
                RecommendationAction.WAIT_COOL_DOWN,
                f"Temperature {alarm.temperature_c}°C exceeds threshold {cls.TEMP_THRESHOLD}°C. Wait for cool-down.",
            )

        # Rule 5: Default action → Reset
        return (
            RecommendationAction.RESET,
            "Conditions allow for automatic reset. No escalation required.",
        )

    @classmethod
    def _check_oscillation(cls, alarm: Alarm, session: Session) -> bool:
        """
        Check if the same alarm code occurred within the oscillation window.

        Args:
            alarm: Current alarm
            session: Database session

        Returns:
            True if oscillation detected
        """
        cutoff_time = alarm.occurred_at - timedelta(minutes=cls.OSCILLATION_WINDOW)

        # Query for same alarm code on same turbine within window
        query = select(Alarm).where(
            Alarm.turbine_db_id == alarm.turbine_db_id,
            Alarm.alarm_code == alarm.alarm_code,
            Alarm.occurred_at >= cutoff_time,
            Alarm.occurred_at < alarm.occurred_at,
            Alarm.id != alarm.id,  # Exclude current alarm
        )

        previous_alarms = session.exec(query).all()
        return len(previous_alarms) > 0

    @classmethod
    def _count_alarms_in_window(
        cls, alarm: Alarm, session: Session, hours: int
    ) -> int:
        """
        Count occurrences of the same alarm code in a time window.

        Args:
            alarm: Current alarm
            session: Database session
            hours: Time window in hours

        Returns:
            Count of alarms
        """
        cutoff_time = alarm.occurred_at - timedelta(hours=hours)

        query = select(Alarm).where(
            Alarm.turbine_db_id == alarm.turbine_db_id,
            Alarm.alarm_code == alarm.alarm_code,
            Alarm.occurred_at >= cutoff_time,
        )

        alarms = session.exec(query).all()
        return len(alarms)

    @classmethod
    def _calculate_avg_temperature(
        cls, alarm: Alarm, session: Session, count: int = 5
    ) -> Optional[float]:
        """
        Calculate average temperature of last N events.

        Args:
            alarm: Current alarm
            session: Database session
            count: Number of recent events to average

        Returns:
            Average temperature or None
        """
        query = (
            select(Alarm)
            .where(
                Alarm.turbine_db_id == alarm.turbine_db_id,
                Alarm.alarm_code == alarm.alarm_code,
                Alarm.temperature_c.is_not(None),
            )
            .order_by(Alarm.occurred_at.desc())
            .limit(count)
        )

        alarms = session.exec(query).all()
        if not alarms:
            return None

        temps = [a.temperature_c for a in alarms if a.temperature_c is not None]
        return sum(temps) / len(temps) if temps else None

    @classmethod
    def generate_recommendation(
        cls, alarm: Alarm, session: Optional[Session] = None
    ) -> dict:
        """
        Generate a recommendation based on alarm code and advanced rules.

        Args:
            alarm: The alarm object to analyze
            session: Database session (optional, for advanced rules)

        Returns:
            Dictionary with recommendation details
        """
        # Determine action and rationale using advanced rules
        action = RecommendationAction.MANUAL_INSPECTION
        rationale = "Manual inspection required."

        if session:
            action, rationale = cls.decide_action(alarm, session)

        # Check if we have a specific rule for this alarm code
        if alarm.alarm_code in cls.ALARM_RULES:
            rule = cls.ALARM_RULES[alarm.alarm_code]

            # Adjust priority based on action
            priority = cls._get_priority_for_action(action, rule["priority"])

            return {
                "alarm_db_id": alarm.id,
                "title": rule["title"],
                "description": rule["description"],
                "priority": priority,
                "action": action,
                "rationale": rationale,
                "action_items": json.dumps(rule["action_items"]),
                "estimated_downtime_hours": rule["estimated_downtime_hours"],
                "is_automated": True,
            }

        # Generate generic recommendation based on severity
        return cls._generate_generic_recommendation(alarm, action, rationale)

    @classmethod
    def _get_priority_for_action(
        cls, action: RecommendationAction, default_priority: RecommendationPriority
    ) -> RecommendationPriority:
        """
        Adjust priority based on action.

        Args:
            action: Recommended action
            default_priority: Default priority from rule

        Returns:
            Adjusted priority
        """
        if action == RecommendationAction.ESCALATE:
            return RecommendationPriority.URGENT
        elif action == RecommendationAction.WAIT_COOL_DOWN:
            return RecommendationPriority.HIGH
        elif action == RecommendationAction.SNOOZE:
            return RecommendationPriority.MEDIUM
        else:
            return default_priority

    @classmethod
    def _generate_generic_recommendation(
        cls,
        alarm: Alarm,
        action: RecommendationAction,
        rationale: str,
    ) -> dict:
        """
        Generate a generic recommendation based on alarm severity.

        Args:
            alarm: The alarm object to analyze
            action: Recommended action
            rationale: Action rationale

        Returns:
            Dictionary with generic recommendation details
        """
        severity_mapping = {
            AlarmSeverity.CRITICAL: {
                "priority": RecommendationPriority.URGENT,
                "action_items": [
                    "Stop turbine operation immediately",
                    "Dispatch emergency maintenance team",
                    "Perform safety inspection",
                    "Contact manufacturer support",
                ],
                "estimated_downtime_hours": 24.0,
            },
            AlarmSeverity.HIGH: {
                "priority": RecommendationPriority.HIGH,
                "action_items": [
                    "Schedule urgent maintenance inspection",
                    "Review recent operational data",
                    "Check related system components",
                    "Reduce turbine load if safe",
                ],
                "estimated_downtime_hours": 12.0,
            },
            AlarmSeverity.MEDIUM: {
                "priority": RecommendationPriority.MEDIUM,
                "action_items": [
                    "Schedule routine maintenance inspection",
                    "Monitor alarm frequency",
                    "Review maintenance history",
                    "Check sensor calibration",
                ],
                "estimated_downtime_hours": 4.0,
            },
            AlarmSeverity.LOW: {
                "priority": RecommendationPriority.LOW,
                "action_items": [
                    "Log alarm for trending analysis",
                    "Monitor during next scheduled maintenance",
                    "Verify sensor readings",
                ],
                "estimated_downtime_hours": 0.0,
            },
        }

        severity_info = severity_mapping.get(
            alarm.severity, severity_mapping[AlarmSeverity.MEDIUM]
        )

        # Adjust priority based on action
        priority = cls._get_priority_for_action(action, severity_info["priority"])

        return {
            "alarm_db_id": alarm.id,
            "title": f"Generic Recommendation for {alarm.alarm_code}",
            "description": f"Standard response for {alarm.severity.value} severity alarm: {alarm.alarm_description}",
            "priority": priority,
            "action": action,
            "rationale": rationale,
            "action_items": json.dumps(severity_info["action_items"]),
            "estimated_downtime_hours": severity_info["estimated_downtime_hours"],
            "is_automated": True,
        }

    @classmethod
    def should_escalate(cls, alarm: Alarm) -> bool:
        """
        Determine if an alarm should be escalated.

        Args:
            alarm: The alarm to evaluate

        Returns:
            True if alarm should be escalated
        """
        # Escalate critical alarms
        if alarm.severity == AlarmSeverity.CRITICAL:
            return True

        # Escalate high severity alarms older than 1 hour
        if alarm.severity == AlarmSeverity.HIGH:
            if (datetime.utcnow() - alarm.occurred_at) > timedelta(hours=1):
                return True

        # Check if alarm is in critical codes list
        critical_codes = ["GEARBOX_TEMP_HIGH", "GRID_DISCONNECT", "PITCH_SYSTEM_FAULT"]
        if alarm.alarm_code in critical_codes:
            return True

        # Not resettable
        if not alarm.resettable:
            return True

        return False

    @classmethod
    def update_turbine_state(
        cls, turbine_id: int, action: RecommendationAction, session: Session
    ) -> None:
        """
        Update turbine state based on recommendation action.

        Args:
            turbine_id: Turbine database ID
            action: Recommended action
            session: Database session
        """
        from app.models import Turbine

        turbine = session.get(Turbine, turbine_id)
        if not turbine:
            return

        old_state = turbine.state

        # Map actions to turbine states
        if action == RecommendationAction.ESCALATE:
            turbine.state = "Faulted"
        elif action == RecommendationAction.WAIT_COOL_DOWN:
            turbine.state = "Cooling"
        elif action == RecommendationAction.RESET:
            turbine.state = "Online"
        elif action == RecommendationAction.SNOOZE:
            turbine.state = "Stopped"
        # MANUAL_INSPECTION keeps current state

        # Update timestamp if state changed
        if turbine.state != old_state:
            turbine.last_state_change = datetime.utcnow()
            turbine.updated_at = datetime.utcnow()
            session.add(turbine)
            session.commit()

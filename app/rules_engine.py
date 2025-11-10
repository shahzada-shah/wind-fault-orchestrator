"""Rules engine for generating recommendations based on alarms."""

import json
from typing import Optional

from app.models import Alarm, AlarmSeverity, Recommendation, RecommendationPriority


class RulesEngine:
    """Business logic for analyzing alarms and generating recommendations."""

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
    }

    @classmethod
    def generate_recommendation(cls, alarm: Alarm) -> Optional[dict]:
        """
        Generate a recommendation based on alarm code.

        Args:
            alarm: The alarm object to analyze

        Returns:
            Dictionary with recommendation details or None if no rule matches
        """
        # Check if we have a specific rule for this alarm code
        if alarm.alarm_code in cls.ALARM_RULES:
            rule = cls.ALARM_RULES[alarm.alarm_code]
            return {
                "alarm_db_id": alarm.id,
                "title": rule["title"],
                "description": rule["description"],
                "priority": rule["priority"],
                "action_items": json.dumps(rule["action_items"]),
                "estimated_downtime_hours": rule["estimated_downtime_hours"],
                "is_automated": True,
            }

        # Generate generic recommendation based on severity
        return cls._generate_generic_recommendation(alarm)

    @classmethod
    def _generate_generic_recommendation(cls, alarm: Alarm) -> dict:
        """
        Generate a generic recommendation based on alarm severity.

        Args:
            alarm: The alarm object to analyze

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

        return {
            "alarm_db_id": alarm.id,
            "title": f"Generic Recommendation for {alarm.alarm_code}",
            "description": f"Standard response for {alarm.severity.value} severity alarm: {alarm.alarm_description}",
            "priority": severity_info["priority"],
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
            from datetime import datetime, timedelta

            if (datetime.utcnow() - alarm.occurred_at) > timedelta(hours=1):
                return True

        # Check if alarm is in critical codes list
        critical_codes = ["GEARBOX_TEMP_HIGH", "GRID_DISCONNECT", "PITCH_SYSTEM_FAULT"]
        if alarm.alarm_code in critical_codes:
            return True

        return False


"""Background worker for periodic tasks like checking snoozed alarms."""

import asyncio
import logging
from datetime import datetime

from sqlmodel import Session, select

from app.db import engine
from app.models import Alarm, Recommendation, RecommendationAction
from app.rules_engine import RulesEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Background worker for periodic maintenance tasks."""

    def __init__(self, check_interval: int = 60):
        """
        Initialize the background worker.

        Args:
            check_interval: Interval in seconds between checks (default: 60)
        """
        self.check_interval = check_interval
        self.running = False

    async def start(self):
        """Start the background worker."""
        self.running = True
        logger.info("Background worker started")

        while self.running:
            try:
                await self.check_snoozed_alarms()
            except Exception as e:
                logger.error(f"Error in background worker: {e}")

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop the background worker."""
        self.running = False
        logger.info("Background worker stopped")

    async def check_snoozed_alarms(self):
        """
        Check for snoozed recommendations that have expired.

        Re-evaluates alarms whose snooze period has ended.
        """
        with Session(engine) as session:
            # Find snoozed recommendations that have expired
            now = datetime.utcnow()
            query = select(Recommendation).where(
                Recommendation.action == RecommendationAction.SNOOZE,
                Recommendation.snooze_until.is_not(None),
                Recommendation.snooze_until <= now,
            )

            expired_recommendations = session.exec(query).all()

            if not expired_recommendations:
                logger.debug("No expired snoozed alarms found")
                return

            logger.info(f"Found {len(expired_recommendations)} expired snoozed alarms")

            for recommendation in expired_recommendations:
                try:
                    # Get the associated alarm
                    alarm = session.get(Alarm, recommendation.alarm_db_id)
                    if not alarm:
                        logger.warning(
                            f"Alarm {recommendation.alarm_db_id} not found for recommendation {recommendation.id}"
                        )
                        continue

                    # Skip if alarm is already resolved
                    if alarm.status in ["resolved", "acknowledged"]:
                        logger.info(
                            f"Alarm {alarm.id} already {alarm.status}, skipping re-evaluation"
                        )
                        continue

                    # Re-evaluate the alarm
                    logger.info(
                        f"Re-evaluating snoozed alarm {alarm.id} (code: {alarm.alarm_code})"
                    )

                    # Generate new recommendation
                    new_recommendation_data = RulesEngine.generate_recommendation(
                        alarm, session
                    )

                    if new_recommendation_data:
                        # Create new recommendation
                        new_recommendation = Recommendation(**new_recommendation_data)
                        session.add(new_recommendation)

                        # Update turbine state if action changed
                        if new_recommendation.action:
                            RulesEngine.update_turbine_state(
                                alarm.turbine_db_id, new_recommendation.action, session
                            )

                        # Mark old recommendation as superseded (by setting snooze_until to None)
                        recommendation.snooze_until = None
                        session.add(recommendation)

                        session.commit()

                        logger.info(
                            f"Created new recommendation {new_recommendation.id} with action: {new_recommendation.action}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error processing recommendation {recommendation.id}: {e}"
                    )
                    session.rollback()
                    continue


# Global worker instance
worker = BackgroundWorker(check_interval=60)  # Check every minute


async def start_background_worker():
    """Start the background worker task."""
    asyncio.create_task(worker.start())
    logger.info("Background worker task created")


def stop_background_worker():
    """Stop the background worker."""
    worker.stop()


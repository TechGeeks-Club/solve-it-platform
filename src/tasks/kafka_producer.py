"""
Kafka Producer Service for Django
Sends code submissions to the judge microservice
"""

import json
import logging
import asyncio
import threading
from datetime import datetime
from typing import Optional
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from django.conf import settings

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """Async Kafka producer for sending submissions"""

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.loop = None

    async def start(self):
        """Initialize and start the Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: str(k).encode("utf-8") if k else None,
                acks="all",
                compression_type="gzip",
                max_batch_size=16384,
                linger_ms=10,
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def send_submission(
        self,
        submission_id: int,
        task_id: int,
        user_id: int,
        team_id: int,
        code: str,
        language_id: int = 50,
    ) -> bool:
        """
        Send a code submission to Kafka

        Args:
            submission_id: TaskSolution ID
            task_id: Task ID
            user_id: Participant user ID
            team_id: Team ID
            code: Source code
            language_id: Judge0 language ID

        Returns:
            bool: True if sent successfully, False otherwise
        """
        logger.debug(f"Attempting to send submission {submission_id} to Kafka")
        logger.debug(
            f"Submission details: task_id={task_id}, user_id={user_id}, team_id={team_id}, language_id={language_id}"
        )
        logger.debug(f"Code length: {len(code)} characters")

        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False

        message = {
            "submission_id": submission_id,
            "task_id": task_id,
            "user_id": user_id,
            "team_id": team_id,
            "code": code,
            "language_id": language_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.debug(
            f"Kafka message payload: {json.dumps({k: v if k != 'code' else f'<{len(v)} chars>' for k, v in message.items()})}"
        )

        try:
            logger.debug(f"Sending to topic: {settings.KAFKA_SUBMISSION_TOPIC}")
            await self.producer.send_and_wait(
                settings.KAFKA_SUBMISSION_TOPIC, value=message, key=submission_id
            )
            logger.info(f"✓ Submission {submission_id} sent to Kafka successfully")
            return True
        except KafkaError as e:
            logger.error(
                f"✗ Kafka error sending submission {submission_id}: {e}", exc_info=True
            )
            return False
        except Exception as e:
            logger.error(
                f"✗ Unexpected error sending submission {submission_id}: {e}",
                exc_info=True,
            )
            return False


# Singleton instance
_producer_instance: Optional[KafkaProducerService] = None


def get_producer() -> KafkaProducerService:
    """Get or create the producer singleton"""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = KafkaProducerService()
    return _producer_instance


def send_submission_sync(
    submission_id: int,
    task_id: int,
    user_id: int,
    team_id: int,
    code: str,
    language_id: int = 50,
) -> bool:
    """
    Non-blocking wrapper for sending submissions from Django views

    Sends the message to Kafka in a background thread to avoid blocking the request
    """

    def _send_in_thread():
        """Background thread function to send to Kafka"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Create a fresh producer instance for this thread
                producer = KafkaProducerService()

                # Start producer
                loop.run_until_complete(producer.start())

                # Send submission
                result = loop.run_until_complete(
                    producer.send_submission(
                        submission_id, task_id, user_id, team_id, code, language_id
                    )
                )

                # Stop producer
                loop.run_until_complete(producer.stop())

                if result:
                    logger.debug(
                        f"Background thread: Successfully sent submission {submission_id}"
                    )
                else:
                    logger.error(
                        f"Background thread: Failed to send submission {submission_id}"
                    )
            finally:
                loop.close()
        except Exception as e:
            logger.error(
                f"Background thread error for submission {submission_id}: {e}",
                exc_info=True,
            )

    # Start background thread to send message
    thread = threading.Thread(target=_send_in_thread, daemon=True)
    thread.start()

    # Return True immediately (optimistic response)
    logger.debug(f"Submission {submission_id} queued for sending in background thread")
    return True

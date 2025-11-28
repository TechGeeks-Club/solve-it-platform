"""
Kafka Producer Service for Django
Sends code submissions to the judge microservice
"""
import json
import logging
import asyncio
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
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                acks='all',
                compression_type='gzip',
                max_batch_size=16384,
                linger_ms=10
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
        language_id: int = 50
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
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        message = {
            'submission_id': submission_id,
            'task_id': task_id,
            'user_id': user_id,
            'team_id': team_id,
            'code': code,
            'language_id': language_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            await self.producer.send_and_wait(
                settings.KAFKA_SUBMISSION_TOPIC,
                value=message,
                key=submission_id
            )
            logger.info(f"Submission {submission_id} sent to Kafka successfully")
            return True
        except KafkaError as e:
            logger.error(f"Kafka error sending submission {submission_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending submission {submission_id}: {e}")
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
    language_id: int = 50
) -> bool:
    """
    Synchronous wrapper for sending submissions from Django views
    
    This function can be called from synchronous Django views
    """
    producer = get_producer()
    
    try:
        # Create new event loop for this thread if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Start producer if not started
        if not producer.producer:
            loop.run_until_complete(producer.start())
        
        # Send submission
        result = loop.run_until_complete(
            producer.send_submission(
                submission_id, task_id, user_id, team_id, code, language_id
            )
        )
        return result
    except Exception as e:
        logger.error(f"Error in send_submission_sync: {e}")
        return False

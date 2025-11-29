"""
Kafka Producers and Consumers for Judge Microservice
"""
import asyncio
import json
import logging
from typing import Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
from pydantic import ValidationError
from config import settings
from models import SubmissionMessage, ResultMessage

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Async Kafka producer for sending results"""
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        
    async def start(self):
        """Initialize and start the producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                acks='all',
                compression_type='gzip'
            )
            await self.producer.start()
            logger.info("Kafka producer started")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop(self):
        """Stop the producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def send_result(self, submission_id: int, result: ResultMessage):
        """Send evaluation result to Kafka"""
        if not self.producer:
            logger.error("Producer not initialized")
            return False
        
        try:
            # Convert Pydantic model to dict
            result_dict = result.model_dump_json_compatible()
            
            await self.producer.send_and_wait(
                settings.KAFKA_RESULT_TOPIC,
                value=result_dict,
                key=submission_id
            )
            logger.info(f"Result for submission {submission_id} sent successfully")
            return True
        except Exception as e:
            logger.error(f"Error sending result for submission {submission_id}: {e}")
            return False

class KafkaConsumer:
    def __init__(self, topic: str, group_id: str):
        self.topic = topic
        self.group_id = group_id
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            session_timeout_ms=30000,        # prevent consumer from being kicked
            heartbeat_interval_ms=3000,
        )
        await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def __aiter__(self):
        # yield messages forever unless stopped
        while True:
            try:
                msg = await self.consumer.getone()  # robust: never ends the loop
                try:
                    validated = SubmissionMessage(**msg.value)
                    yield validated
                except ValidationError as e:
                    logger.error(f"Invalid message format: {e}")
            except KafkaError as e:
                logger.error(f"Kafka error: {e}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(1)


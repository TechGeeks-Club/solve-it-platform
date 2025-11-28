"""
Kafka Producers and Consumers for Judge Microservice
"""
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
    """Async Kafka consumer for receiving submissions"""
    
    def __init__(self, topic: str, group_id: str):
        self.topic = topic
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        
    async def start(self):
        """Initialize and start the consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            await self.consumer.start()
            logger.info(f"Kafka consumer started for topic: {self.topic}")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise
    
    async def stop(self):
        """Stop the consumer"""
        if self.consumer:
            await self.consumer.stop()
            logger.info(f"Kafka consumer stopped for topic: {self.topic}")
    
    async def __aiter__(self):
        """Make the consumer async iterable with Pydantic validation"""
        async for message in self.consumer:
            try:
                # Validate message with Pydantic model
                validated_message = SubmissionMessage(**message.value)
                yield message._replace(value=validated_message)
            except ValidationError as e:
                logger.error(f"Invalid message format: {e}")
                logger.error(f"Raw message: {message.value}")
                # Skip invalid messages
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue

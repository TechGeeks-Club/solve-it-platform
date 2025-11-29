"""
Main Judge Microservice
Handles async consumption of submissions, evaluation, and result publishing
"""
import asyncio
import logging
import signal
from typing import List
from datetime import datetime

from database import DatabaseClient
from judge_client import Judge0Client
from kafka_client import KafkaConsumer, KafkaProducer
from models import SubmissionMessage, ResultMessage, ExecutionResult
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logs from third-party libraries
logging.getLogger('aiokafka').setLevel(logging.WARNING)
logging.getLogger('kafka').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


class JudgeService:
    """Main service orchestrator"""
    
    def __init__(self):
        self.db_client = DatabaseClient()
        self.judge_client = Judge0Client()
        self.producer = KafkaProducer()
        self.submission_consumer = KafkaConsumer(
            settings.KAFKA_SUBMISSION_TOPIC,
            'judge-service-group'
        )
        self.running = False
        
    async def start(self):
        """Start all clients"""
        logger.info("Starting Judge Service...")
        
        await self.db_client.connect()
        await self.judge_client.start()
        await self.producer.start()
        await self.submission_consumer.start()
        
        self.running = True
        logger.info("Judge Service started successfully")
    
    async def stop(self):
        """Stop all clients"""
        logger.info("Stopping Judge Service...")
        self.running = False
        
        await self.submission_consumer.stop()
        await self.producer.stop()
        await self.judge_client.stop()
        await self.db_client.close()
        
        logger.info("Judge Service stopped")
    
    async def process_submission(self, message: SubmissionMessage):
        """
        Process a single code submission
        
        Args:
            message: Submission message from Kafka (Pydantic model)
        """
        logger.info(
            f"Processing submission {message.submission_id} for task {message.task_id} "
            f"by user {message.user_id} (team {message.team_id})"
        )
        logger.debug(f"Submission details: language_id={message.language_id}, code_length={len(message.code)} chars")
        logger.debug(f"Code preview: {message.code[:200]}..." if len(message.code) > 200 else f"Code: {message.code}")
        
        try:
            # Fetch test cases from database (with caching)
            logger.debug(f"Fetching test cases for task {message.task_id}")
            test_cases = await self.db_client.get_test_cases(message.task_id)
            
            if not test_cases:
                logger.error(f"No test cases found for task {message.task_id}")
                result = ResultMessage(
                    submission_id=message.submission_id,
                    task_id=message.task_id,
                    user_id=message.user_id,
                    team_id=message.team_id,
                    status='failed',
                    error_message='No test cases available for this task',
                    score=0,
                    passed_tests=0,
                    total_tests=0
                )
                await self.producer.send_result(message.submission_id, result)
                return
            
            logger.info(f"Found {len(test_cases)} test cases for task {message.task_id}")
            
            # Execute code against test cases
            execution_result = await self.judge_client.execute_code(
                message.code,
                message.language_id,
                test_cases
            )
            
            # Create result message using Pydantic model
            result = ResultMessage(
                submission_id=message.submission_id,
                task_id=message.task_id,
                user_id=message.user_id,
                team_id=message.team_id,
                **execution_result,
                processed_at=datetime.utcnow()
            )
            
            # Send result to Kafka
            await self.producer.send_result(message.submission_id, result)
            
            logger.info(
                f"Submission {message.submission_id} completed: "
                f"{result.passed_tests}/{result.total_tests} tests passed, "
                f"score: {result.score}"
            )
            
        except Exception as e:
            logger.error(f"Error processing submission {message.submission_id}: {e}", exc_info=True)
            
            # Send error result using Pydantic model
            error_result = ResultMessage(
                submission_id=message.submission_id,
                task_id=message.task_id,
                user_id=message.user_id,
                team_id=message.team_id,
                status='failed',
                error_message=str(e),
                score=0,
                passed_tests=0,
                total_tests=0
            )
            await self.producer.send_result(message.submission_id, error_result)


async def submission_consumer_loop(service: JudgeService):
    """
    Consumer loop for processing code submissions
    """
    logger.info("Submission consumer loop started")
    logger.info(f"Listening on topic: {settings.KAFKA_SUBMISSION_TOPIC}")
    logger.info(f"Kafka servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    
    try:
        async for message in service.submission_consumer:
            if not service.running:
                logger.info("Service stopping, breaking consumer loop")
                break
            
            logger.debug(f"Received message for submission {message.submission_id}")
            
            try:
                await service.process_submission(message)
            except Exception as e:
                logger.error(f"Error processing submission {message.submission_id}: {e}", exc_info=True)
                # Continue processing next message instead of stopping
                continue
                
    except asyncio.CancelledError:
        logger.info("Consumer loop cancelled")
    except Exception as e:
        logger.error(f"Fatal error in submission consumer loop: {e}", exc_info=True)
        # Don't raise - let the service continue
    
    logger.info("Submission consumer loop stopped")


async def main():
    """Main entry point"""
    service = JudgeService()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler():
        logger.info("Received shutdown signal")
        service.running = False
    
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Start the service
        await service.start()
        
        logger.info("Starting consumer loop")
        
        # Keep running until explicitly stopped
        while service.running:
            try:
                # Run consumer loop
                await submission_consumer_loop(service)
                
                # If we get here and service is still running, the loop exited unexpectedly
                if service.running:
                    logger.warning("Consumer loop exited unexpectedly, restarting in 5 seconds...")
                    await asyncio.sleep(5)
                    
            except asyncio.CancelledError:
                logger.info("Consumer loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in consumer loop, restarting in 5 seconds: {e}", exc_info=True)
                await asyncio.sleep(5)
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
    finally:
        # Cleanup
        await service.stop()
        logger.info("Service shutdown complete")


if __name__ == '__main__':
    asyncio.run(main())

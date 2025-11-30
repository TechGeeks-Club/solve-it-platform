"""
Kafka Consumer Service for Django
Receives results from judge microservice and saves to database
"""
import json
import logging
import asyncio
from typing import Optional
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from django.conf import settings
import django
from django.utils import timezone

logger = logging.getLogger(__name__)


class KafkaConsumerService:
    """Async Kafka consumer for receiving judge results"""
    
    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        
    async def start(self):
        """Initialize and start the Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                settings.KAFKA_RESULT_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id='django-result-consumer',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            await self.consumer.start()
            logger.info("Kafka consumer started successfully")
            self.running = True
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise
    
    async def stop(self):
        """Stop the Kafka consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
    
    async def consume_results(self):
        """
        Main loop to consume and process results
        """
        from tasks.models import TaskSolution  # Import here to avoid circular imports
        
        logger.info("Starting to consume results from Kafka...")
        logger.debug(f"Listening on topic: {settings.KAFKA_RESULT_TOPIC}")
        
        try:
            async for message in self.consumer:
                if not self.running:
                    logger.info("Consumer stopping, breaking loop")
                    break
                    
                try:
                    result = message.value
                    submission_id = result.get('submission_id')
                    
                    logger.info(f"📨 Received result for submission {submission_id}")
                    logger.debug(f"Result data: status={result.get('status')}, score={result.get('score')}, passed={result.get('passed_tests')}/{result.get('total_tests')}")
                    
                    # Get the submission from database
                    try:
                        submission = await asyncio.to_thread(
                            TaskSolution.objects.select_related('task').get,
                            id=submission_id
                        )
                        logger.debug(f"Found submission {submission_id} in database")
                    except TaskSolution.DoesNotExist:
                        logger.error(f"❌ Submission {submission_id} not found in database")
                        continue
                    
                    # Get task tests with display flags
                    from tasks.models import TaskTest
                    task_tests = await asyncio.to_thread(
                        lambda: list(TaskTest.objects.filter(task=submission.task).order_by('order', 'id').values('id', 'display', 'input', 'output'))
                    )
                    
                    # Enrich test results with display flag and test data
                    test_results = result.get('test_results', [])
                    enriched_results = []
                    for idx, test_result in enumerate(test_results):
                        enriched_test = test_result.copy()
                        if idx < len(task_tests):
                            enriched_test['display'] = task_tests[idx]['display']
                            enriched_test['input'] = task_tests[idx]['input']
                            enriched_test['expected_output'] = task_tests[idx]['output']
                        else:
                            enriched_test['display'] = False
                        enriched_results.append(enriched_test)
                    
                    # Update submission with results
                    submission.passed_tests = result.get('passed_tests', 0)
                    submission.total_tests = result.get('total_tests', 0)
                    submission.score = result.get('score', 0)
                    submission.test_results = enriched_results
                    submission.compiler_output = result.get('compiler_output', '')
                    submission.error_message = result.get('error_message', '')
                    submission.processing_completed_at = timezone.now()
                    
                    # Determine status based on score and threshold
                    from tasks.models import Settings
                    app_settings = await asyncio.to_thread(Settings.get_settings)
                    if submission.score >= app_settings.pass_threshold:
                        submission.status = 'completed'
                    else:
                        submission.status = 'failed'
                    
                    # Generate correction ID
                    submission.correction_id = f"{submission_id}_{int(timezone.now().timestamp())}"
                    
                    # if submission.score and submission.score > 0:
                    submission.is_corrected = True
                    
                    # Save to database
                    await asyncio.to_thread(submission.save)
                    # submission.save()
                    
                    # Award coins for 100% completion
                    if submission.score == 100 and submission.status == 'completed':
                        from registration.models import Team
                        team = await asyncio.to_thread(
                            lambda: Team.objects.get(id=submission.team.id)
                        )
                        coins_awarded = submission.task.coins
                        team.coins += coins_awarded
                        await asyncio.to_thread(team.save)
                        logger.info(f"💰 Awarded {coins_awarded} coins to team {team.name} for 100% completion")
                    
                    logger.info(
                        f"✓ Submission {submission_id} updated: "
                        f"{submission.passed_tests}/{submission.total_tests} tests passed, "
                        f"score: {submission.score}%"
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Error processing result message: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"❌ Error in consume_results loop: {e}", exc_info=True)
        finally:
            await self.stop()


async def result_consumer_loop():
    """
    Standalone async function to run the result consumer
    This should be run in a separate process or management command
    """
    consumer = KafkaConsumerService()
    
    try:
        await consumer.start()
        await consumer.consume_results()
    except KeyboardInterrupt:
        logger.info("Result consumer interrupted")
    finally:
        await consumer.stop()


if __name__ == '__main__':
    # Setup Django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
    django.setup()
    
    # Run the consumer
    asyncio.run(result_consumer_loop())

"""
Database Client for fetching test cases from Django PostgreSQL
Uses async connection pooling and Redis caching
"""
import json
import logging
import asyncpg
import redis.asyncio as redis
from typing import List, Dict, Optional
from config import settings

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Async database client with Redis caching"""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Initialize database pool and Redis connection"""
        try:
            # Create PostgreSQL connection pool
            self.db_pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                min_size=2,
                max_size=10
            )
            logger.info("Database pool created successfully")
            
            # Create Redis connection
            self.redis_client = await redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            logger.info("Redis client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to database/redis: {e}")
            raise
    
    async def close(self):
        """Close database pool and Redis connection"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database pool closed")
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis client closed")
    
    async def get_test_cases(self, task_id: int) -> List[Dict]:
        """
        Get test cases for a task with Redis caching
        
        Args:
            task_id: Task ID
            
        Returns:
            List of test case dictionaries with 'input' and 'expected_output'
        """
        cache_key = f"task:{task_id}:tests"
        
        # Try Redis cache first
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.info(f"Cache hit for task {task_id} tests")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")
        
        # Cache miss - fetch from database
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, input, output, weight, is_sample, display
                    FROM tasks_tasktest
                    WHERE task_id = $1
                    ORDER BY "order", id
                    """,
                    task_id
                )
                
                test_cases = [
                    {
                        'id': row['id'],
                        'input': row['input'] or '',
                        'expected_output': row['output'],
                        'weight': row['weight'],
                        'is_sample': row['is_sample'],
                        'display': row['display']
                    }
                    for row in rows
                ]
                
                # Cache for future use
                try:
                    await self.redis_client.setex(
                        cache_key,
                        settings.REDIS_CACHE_TTL,
                        json.dumps(test_cases)
                    )
                except Exception as e:
                    logger.warning(f"Redis cache write error: {e}")
                
                logger.info(f"Fetched {len(test_cases)} test cases for task {task_id} from database")
                return test_cases
                
        except Exception as e:
            logger.error(f"Error fetching test cases for task {task_id}: {e}")
            return []
    
    async def get_task_info(self, task_id: int) -> Optional[Dict]:
        """
        Get basic task information
        
        Args:
            task_id: Task ID
            
        Returns:
            Dictionary with task info or None
        """
        cache_key = f"task:{task_id}:info"
        
        # Try cache first
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")
        
        # Fetch from database
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, title, points, level
                    FROM tasks_task
                    WHERE id = $1
                    """,
                    task_id
                )
                
                if row:
                    task_info = {
                        'id': row['id'],
                        'title': row['title'],
                        'points': row['points'],
                        'level': row['level']
                    }
                    
                    # Cache it
                    try:
                        await self.redis_client.setex(
                            cache_key,
                            settings.REDIS_CACHE_TTL,
                            json.dumps(task_info)
                        )
                    except Exception as e:
                        logger.warning(f"Redis cache write error: {e}")
                    
                    return task_info
                return None
                
        except Exception as e:
            logger.error(f"Error fetching task info for task {task_id}: {e}")
            return None

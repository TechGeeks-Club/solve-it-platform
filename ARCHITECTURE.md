# Architecture Overview - Solve-IT Platform with Judge0 Integration

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx (Port 80)                         │
│              Reverse Proxy + Static File Server                │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌───────────────┐                 ┌──────────────┐
│    Django     │                 │    Static    │
│ Application   │                 │    Files     │
│  (Port 8000)  │                 │              │
└───────┬───────┘                 └──────────────┘
        │
        │  Submits Code
        ▼
┌────────────────────────────────────────────────┐
│              Kafka (KRaft Mode)                │
│          Topic: code-submissions               │
└────────┬───────────────────────────────────────┘
         │
         │  Consumes Submissions
         ▼
┌─────────────────────────────────────────────────┐
│         Judge Microservice (Async)              │
│  ┌──────────────────────────────────────────┐   │
│  │  Submission Consumer Loop                │   │
│  │    ├─> Fetch Test Cases (PostgreSQL)    │   │
│  │    │   └─> Redis Cache Layer            │   │
│  │    ├─> Execute Code (Judge0 API)        │   │
│  │    └─> Calculate Score                  │   │
│  └──────────────────────────────────────────┘   │
└────────┬────────────────────────────────────────┘
         │
         │  Sends Results
         ▼
┌────────────────────────────────────────────────┐
│              Kafka (KRaft Mode)                │
│            Topic: code-results                 │
└────────┬───────────────────────────────────────┘
         │
         │  Consumes Results
         ▼
┌─────────────────────────────────────────────────┐
│     Django Consumer (Management Command)        │
│          Updates TaskSolution in DB             │
└─────────────────────────────────────────────────┘


                Supporting Services
        ┌──────────────────────────────────┐
        │  Judge0 Server + Workers         │
        │    (Code Execution Engine)       │
        └──────────────────────────────────┘
        ┌──────────────────────────────────┐
        │  Redis (Caching + Judge0 Queue)  │
        └──────────────────────────────────┘
        ┌──────────────────────────────────┐
        │  PostgreSQL (Judge0 DB)          │
        └──────────────────────────────────┘
        ┌──────────────────────────────────┐
        │  PostgreSQL (Django DB)          │
        └──────────────────────────────────┘
```

## Data Flow

### 1. Code Submission Flow
```
User → Django View → Create TaskSolution (status='pending')
                  → Send to Kafka ('code-submissions' topic)
                  → Update status to 'processing'
                  → Return success message
```

### 2. Code Evaluation Flow
```
Kafka → Judge Microservice → Fetch Test Cases (DB + Redis Cache)
                           → Execute Code (Judge0 API)
                           → Calculate Score
                           → Send Result to Kafka ('code-results' topic)
```

### 3. Result Processing Flow
```
Kafka → Django Consumer → Fetch TaskSolution from DB
                        → Update with results
                        → Save to database
```

## Components

### 1. Django Application
**Location:** `/src`

**Responsibilities:**
- Web interface and API
- User authentication
- Task management
- Submission creation
- Result display

**Key Files:**
- `tasks/models.py` - Enhanced with Judge0 fields
- `tasks/views.py` - Updated to send to Kafka
- `tasks/kafka_producer.py` - Async Kafka producer
- `tasks/kafka_consumer.py` - Async Kafka consumer
- `tasks/management/commands/consume_results.py` - Consumer command

**New Model Fields (TaskSolution):**
```python
code = TextField()  # Source code
language_id = IntegerField()  # Judge0 language ID
status = CharField()  # pending, processing, completed, failed
kafka_sent_at = DateTimeField()
processing_started_at = DateTimeField()
processing_completed_at = DateTimeField()
execution_time = FloatField()
memory_used = FloatField()
passed_tests = IntegerField()
total_tests = IntegerField()
test_results = JSONField()  # Detailed results
compiler_output = TextField()
error_message = TextField()
```

**New Model Fields (TaskTest):**
```python
weight = IntegerField()  # For weighted scoring
is_sample = BooleanField()
order = IntegerField()
```

### 2. Judge Microservice
**Location:** `/judge-microservice`

**Responsibilities:**
- Consume submissions from Kafka
- Fetch test cases from PostgreSQL
- Cache test cases in Redis
- Execute code via Judge0
- Calculate weighted scores
- Send results back to Kafka

**Architecture:**
- **config.py** - Configuration management
- **database.py** - Async PostgreSQL client with Redis caching
- **judge_client.py** - Judge0 API client using aiohttp
- **kafka_client.py** - Kafka producer and consumer
- **main.py** - Service orchestrator with async loops

**Consumer Loop:**
```python
tasks = [
    asyncio.create_task(submission_consumer_loop(service)),
]
```

### 3. Kafka (KRaft Mode)
**Topics:**
- `code-submissions` - From Django to Judge Service
- `code-results` - From Judge Service to Django

**Message Format (Submission):**
```json
{
  "submission_id": 123,
  "task_id": 45,
  "user_id": 67,
  "team_id": 89,
  "code": "source code here",
  "language_id": 50,
  "timestamp": "2025-11-28T12:00:00Z"
}
```

**Message Format (Result):**
```json
{
  "submission_id": 123,
  "task_id": 45,
  "status": "completed",
  "score": 85,
  "passed_tests": 17,
  "total_tests": 20,
  "execution_time": 0.234,
  "memory_used": 2048,
  "test_results": [...],
  "compiler_output": "",
  "error_message": "",
  "processed_at": "2025-11-28T12:00:05Z"
}
```

### 4. Judge0
**Purpose:** Code execution engine

**Components:**
- **judge0-server** - API server
- **judge0-worker** - Execution workers
- **judge0-db** - PostgreSQL database
- **redis** - Queue management

**Supported Languages:** 60+ (C, C++, Python, Java, JavaScript, etc.)

### 5. Redis
**Uses:**
- Test case caching (1 hour TTL)
- Task info caching
- Judge0 queue management

### 6. Nginx
**Purpose:** Reverse proxy and static file server

**Routes:**
- `/` → Django application
- `/static/` → Static files (with caching)
- `/media/` → Media files

## Docker Services

| Service | Container Name | Purpose |
|---------|---------------|---------|
| nginx | solve-it-nginx | Reverse proxy |
| django | solve-it-django | Web application |
| django-consumer | solve-it-django-consumer | Result consumer |
| judge-microservice | solve-it-judge-microservice | Code evaluation |
| kafka | solve-it-kafka | Message broker |
| redis | solve-it-redis | Cache + Judge0 queue |
| judge0-server | solve-it-judge0-server | Code execution API |
| judge0-worker | solve-it-judge0-worker | Code execution workers |
| judge0-db | solve-it-judge0-db | Judge0 database |
| db | solve-it-db | Django database (optional) |

## Technology Stack

### Backend
- **Django 5.1.3** - Web framework
- **Gunicorn** - WSGI server
- **aiokafka 0.10.0** - Async Kafka client
- **aiohttp 3.9.1** - Async HTTP client
- **asyncpg 0.29.0** - Async PostgreSQL driver
- **redis 5.0.1** - Redis client

### Microservice
- **Python 3.11** - Runtime
- **asyncio** - Async framework
- **Judge0 API** - Code execution

### Infrastructure
- **Apache Kafka (KRaft)** - Message broker
- **Judge0 1.13.0** - Code execution engine
- **Redis 7** - Cache and queue
- **PostgreSQL 15** - Database
- **Nginx** - Reverse proxy

## Development Workflow

### Local Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f django
docker-compose logs -f judge-microservice
docker-compose logs -f django-consumer

# Run migrations
docker-compose exec django python manage.py makemigrations
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createsuperuser
```

### Testing Submissions
1. Login to the platform
2. Select a task
3. Submit code (file upload or direct input)
4. Code is sent to Kafka
5. Judge microservice processes it
6. Results are saved back to database
7. View results on the platform

## Monitoring

### Check Service Health
```bash
# All services
docker-compose ps

# Specific service logs
docker-compose logs -f judge-microservice
docker-compose logs -f django-consumer

# Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# View Kafka messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic code-submissions \
  --from-beginning
```

### Database Queries
```bash
# Connect to Django database
docker-compose exec django python manage.py dbshell

# Check submissions
SELECT id, status, score, passed_tests, total_tests 
FROM tasks_tasksolution 
ORDER BY submitted_at DESC LIMIT 10;
```

## Performance Optimizations

1. **Redis Caching**: Test cases are cached for 1 hour
2. **Async Processing**: All I/O operations are async
3. **Kafka**: Decouples submission from evaluation
4. **Connection Pooling**: PostgreSQL connection pool
5. **Weighted Scoring**: Test cases can have different weights

## Security Considerations

1. **Code Isolation**: Judge0 runs code in isolated containers
2. **Resource Limits**: Execution time and memory limits
3. **Input Validation**: All inputs are validated
4. **Authentication**: Required for submissions
5. **CORS**: Properly configured

## Next Steps

1. **Add PostgreSQL**: Switch from SQLite to PostgreSQL for production
2. **Add Monitoring**: Prometheus + Grafana for metrics
3. **Add Logging**: Centralized logging with ELK stack
4. **Add Tests**: Unit and integration tests
5. **Add CI/CD**: Automated deployment pipeline
6. **Add Rate Limiting**: Prevent abuse
7. **Add Leaderboard**: Real-time rankings

## Troubleshooting

### Kafka Connection Issues
```bash
# Check Kafka is running
docker-compose ps kafka

# Recreate Kafka
docker-compose restart kafka
```

### Judge0 Not Responding
```bash
# Check Judge0 services
docker-compose ps judge0-server judge0-worker

# Restart Judge0
docker-compose restart judge0-server judge0-worker
```

### Database Connection Issues
```bash
# Check database
docker-compose ps db

# View database logs
docker-compose logs db
```

## References

- [Judge0 Documentation](https://ce.judge0.com/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [aiokafka Documentation](https://aiokafka.readthedocs.io/)
- [Django Documentation](https://docs.djangoproject.com/)

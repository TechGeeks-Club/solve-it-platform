# Migration Guide - Upgrading to Judge0 Integration

## Overview

This guide helps you migrate your existing Solve-IT platform to the new Judge0-powered automatic evaluation system.

## Database Changes

### Required Migrations

The following model changes need to be migrated:

**TaskTest Model:**
- Added `weight` field (default: 1)
- Added `is_sample` field
- Added `order` field

**TaskSolution Model:**
- Changed `code` from FileField to TextField
- Added `code_file` field (FileField, optional)
- Added `language_id` field
- Added `kafka_sent_at` field
- Added `processing_started_at` field
- Added `processing_completed_at` field
- Removed `judge0_token` field
- Enhanced `test_results` to use JSONField with default=list

### Run Migrations

```bash
# Inside Docker container
docker-compose exec django python manage.py makemigrations tasks
docker-compose exec django python manage.py migrate

# Or locally
cd src
python manage.py makemigrations tasks
python manage.py migrate
```

## Data Migration

### Migrate Existing Submissions

If you have existing submissions with file uploads, you may want to convert them to text:

```python
# Django shell
docker-compose exec django python manage.py shell

from tasks.models import TaskSolution

# Convert file-based submissions to text
for submission in TaskSolution.objects.filter(code_file__isnull=False, code__isnull=True):
    try:
        with submission.code_file.open('r') as f:
            submission.code = f.read()
            submission.save()
        print(f"Migrated submission {submission.id}")
    except Exception as e:
        print(f"Error migrating submission {submission.id}: {e}")
```

### Update Test Cases

Add weights to existing test cases:

```python
from tasks.models import TaskTest

# Set all existing tests to weight=1, order by ID
for idx, test in enumerate(TaskTest.objects.all().order_by('id')):
    test.weight = 1
    test.order = idx
    test.save()
```

## Configuration Changes

### Environment Variables

Update your `.env` file with new variables:

```env
# Judge Microservice Database Access
DB_HOST=db
DB_PORT=5432
DB_NAME=solveitdb
DB_USER=solveit
DB_PASSWORD=solveit123

# Redis Configuration
REDIS_DB=0
REDIS_CACHE_TTL=3600

# Judge0 Configuration
JUDGE0_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
```

### Kafka Topics

The system uses two Kafka topics:
- `code-submissions` - Created automatically
- `code-results` - Created automatically

No manual topic creation needed (auto-create is enabled).

## Deployment Steps

### Step 1: Stop Current Services

```bash
docker-compose down
```

### Step 2: Backup Database

```bash
# Backup SQLite database
cp src/db.sqlite3 src/db.sqlite3.backup

# Or export data
docker-compose exec django python manage.py dumpdata > backup.json
```

### Step 3: Pull Latest Code

```bash
git pull origin master
# Or download the latest code
```

### Step 4: Build New Images

```bash
docker-compose build
```

### Step 5: Start Services

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Step 6: Run Migrations

```bash
docker-compose exec django python manage.py migrate
```

### Step 7: Verify Services

```bash
# Check all services are running
docker-compose ps

# Should see:
# - nginx
# - django
# - django-consumer
# - judge-microservice
# - kafka
# - redis
# - judge0-server
# - judge0-worker
# - judge0-db
# - db
```

## Testing the Integration

### 1. Create Test Task

```python
docker-compose exec django python manage.py shell

from tasks.models import Task, TaskTest, Phase

# Create a simple task
phase = Phase.objects.first()  # or create one
task = Task.objects.create(
    phase=phase,
    title="Test Task",
    context="Write a program that prints 'Hello World'",
    points=100,
    level="easy"
)

# Add test case
TaskTest.objects.create(
    task=task,
    input="",
    output="Hello World\n",
    weight=1,
    display=True,
    is_sample=True,
    order=0
)
```

### 2. Submit Test Code

Via web interface or:

```python
from tasks.models import TaskSolution
from registration.models import Participant
from tasks.kafka_producer import send_submission_sync

participant = Participant.objects.first()
code = "#include <stdio.h>\nint main() { printf(\"Hello World\\n\"); return 0; }"

submission = TaskSolution.objects.create(
    task=task,
    participant=participant,
    team=participant.team,
    code=code,
    language_id=50,  # C
    status='pending'
)

# Send to Kafka
send_submission_sync(
    submission_id=submission.id,
    task_id=task.id,
    user_id=participant.user.id,
    team_id=participant.team.id,
    code=code,
    language_id=50
)
```

### 3. Monitor Processing

```bash
# Watch judge microservice logs
docker-compose logs -f judge-microservice

# Watch consumer logs
docker-compose logs -f django-consumer

# Check submission status
docker-compose exec django python manage.py shell
>>> from tasks.models import TaskSolution
>>> sub = TaskSolution.objects.last()
>>> print(f"Status: {sub.status}, Score: {sub.score}")
```

## Rollback Procedure

If you need to rollback:

### Step 1: Stop Services
```bash
docker-compose down
```

### Step 2: Restore Database
```bash
# Restore SQLite backup
cp src/db.sqlite3.backup src/db.sqlite3

# Or restore from JSON dump
docker-compose up -d django
docker-compose exec django python manage.py loaddata backup.json
```

### Step 3: Revert Code
```bash
git checkout <previous-commit>
# Or restore previous code version
```

### Step 4: Rebuild and Start
```bash
docker-compose build
docker-compose up -d
```

## Common Issues

### Issue: Judge Microservice Can't Connect to Database

**Solution:**
Check that the database credentials in `.env` match the PostgreSQL settings. If using SQLite, the judge microservice needs to be configured differently (not recommended for production).

### Issue: Kafka Connection Timeout

**Solution:**
```bash
# Restart Kafka
docker-compose restart kafka

# Wait for it to be healthy
docker-compose ps kafka
```

### Issue: Consumer Not Processing Results

**Solution:**
```bash
# Check consumer is running
docker-compose ps django-consumer

# Restart consumer
docker-compose restart django-consumer

# View logs
docker-compose logs -f django-consumer
```

### Issue: Judge0 Execution Timeout

**Solution:**
Increase timeout in `.env`:
```env
JUDGE0_TIMEOUT=60
```

Then restart:
```bash
docker-compose restart judge-microservice
```

## Performance Tuning

### 1. Increase Judge0 Workers
Edit `docker-compose.yml`:
```yaml
judge0-worker:
  deploy:
    replicas: 3  # Add multiple worker instances
```

### 2. Increase Kafka Partitions
```bash
docker-compose exec kafka kafka-topics --alter \
  --bootstrap-server localhost:9092 \
  --topic code-submissions \
  --partitions 8
```

### 3. Tune Redis Cache
Increase TTL in `.env`:
```env
REDIS_CACHE_TTL=7200  # 2 hours
```

### 4. Scale Django Consumers
Edit `docker-compose.yml`:
```yaml
django-consumer:
  deploy:
    replicas: 2  # Add multiple consumer instances
```

## Monitoring Setup

### View Real-time Metrics

```bash
# Service resource usage
docker stats

# Kafka lag
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group judge-service-group
```

### Set Up Logging

Add to `docker-compose.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Support

For issues:
1. Check logs: `docker-compose logs -f <service>`
2. Verify environment variables in `.env`
3. Check service health: `docker-compose ps`
4. Review ARCHITECTURE.md for system details

## Next Steps After Migration

1. ✅ Test with real submissions
2. ✅ Monitor performance
3. ✅ Set up backups
4. ✅ Configure alerts
5. ✅ Document custom workflows
6. ✅ Train users on new features

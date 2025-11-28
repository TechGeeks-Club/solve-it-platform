# Pydantic Models and Settings for Judge Microservice

## Overview

The judge microservice now uses Pydantic for both message validation and configuration management:

- **Message Models**: Type-safe Kafka message handling
- **Settings**: Validated configuration with Pydantic Settings

This provides:

- **Type Safety**: Automatic validation of messages and config
- **Error Handling**: Invalid data is caught early with clear errors
- **Documentation**: Self-documenting schemas
- **IDE Support**: Better autocomplete and type hints
- **Environment Variables**: Automatic loading from .env files

## Installation

Before running the service, install the required dependencies:

```bash
cd /home/amar/solve-it-platform/judge-microservice

# Create a virtual environment (if not already created)
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
.\venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your actual configuration values
```

## Configuration with Pydantic Settings

The service now uses Pydantic Settings for type-safe configuration management.

### Configuration File

Create a `.env` file in the `judge-microservice` directory:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SUBMISSION_TOPIC=code-submissions
KAFKA_RESULT_TOPIC=code-results

# Judge0 Configuration
JUDGE0_API_URL=http://localhost:2358
JUDGE0_TIMEOUT=30

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_CACHE_TTL=3600

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=solveitdb
DB_USER=solveit
DB_PASSWORD=solveit123

# Logging
LOG_LEVEL=INFO
```

### Benefits of Pydantic Settings

1. **Type Validation**: All configuration values are validated at startup
2. **Default Values**: Sensible defaults with Field descriptions
3. **Environment Variables**: Automatic loading from .env file
4. **Type Conversion**: Automatic conversion (e.g., string to int)
5. **Custom Validation**: Port ranges, log levels, etc. are validated
6. **Error Messages**: Clear errors if configuration is invalid

### Usage in Code

```python
from config import settings

# Access configuration with type safety
print(settings.kafka_bootstrap_servers)  # List[str]
print(settings.judge0_timeout)  # int
print(settings.database_url)  # Property: full connection string
print(settings.redis_url)  # Property: redis://localhost:6379/0

# Backward compatible
from config import KAFKA_BOOTSTRAP_SERVERS, LOG_LEVEL
```

## Message Models

### SubmissionMessage

Represents an incoming submission from Kafka:

```python
{
    "submission_id": 123,
    "task_id": 5,
    "user_id": 42,
    "team_id": 7,  # Optional
    "code": "#include <stdio.h>\nint main() { return 0; }",
    "language_id": 50  # Default: 50 (C language)
}
```

**Validation Rules:**
- `submission_id`: Required integer
- `task_id`: Required integer
- `user_id`: Required integer
- `team_id`: Optional integer
- `code`: Required string (min length: 1)
- `language_id`: Integer (default: 50)

### ResultMessage

Represents an outgoing result sent to Kafka:

```python
{
    "submission_id": 123,
    "task_id": 5,
    "user_id": 42,
    "team_id": 7,  # Optional
    "status": "completed",
    "score": 85.5,
    "passed_tests": 4,
    "total_tests": 5,
    "test_results": None,  # Optional detailed results
    "error_message": None,  # Optional error message
    "processed_at": "2025-11-28T12:00:00Z"
}
```

**Validation Rules:**
- `score`: Float between 0.0 and 100.0
- `passed_tests`: Integer >= 0, cannot exceed `total_tests`
- `total_tests`: Integer >= 0
- `processed_at`: Automatically set to current UTC time

## Benefits

### 1. Automatic Validation

Invalid messages are automatically caught and logged:

```python
# Invalid message (missing required field)
{
    "submission_id": 123,
    # Missing task_id, user_id, and code
}
# → ValidationError logged, message skipped
```

### 2. Type Safety

```python
# Before (dict-based)
submission_id = message.get('submission_id')  # Could be None
task_id = message.get('task_id')  # Type unknown

# After (Pydantic)
submission_id = message.submission_id  # Guaranteed to exist
task_id = message.task_id  # Type-checked as int
```

### 3. Documentation

Models serve as self-documenting schemas with examples and field descriptions.

### 4. Better Error Messages

Pydantic provides detailed validation errors:

```
Invalid message format: 2 validation errors for SubmissionMessage
task_id
  field required (type=value_error.missing)
code
  ensure this value has at least 1 characters (type=value_error.any_str.min_length; limit_value=1)
```

## Usage Examples

### Consumer Side

```python
async for message in service.submission_consumer:
    # message.value is now a SubmissionMessage Pydantic model
    submission = message.value
    
    # Type-safe access
    print(f"Processing submission {submission.submission_id}")
    print(f"Code length: {len(submission.code)}")
    print(f"Language: {submission.language_id}")
```

### Producer Side

```python
# Create result message
result = ResultMessage(
    submission_id=123,
    task_id=5,
    user_id=42,
    team_id=7,
    status='completed',
    score=85.5,
    passed_tests=4,
    total_tests=5
)

# Send to Kafka (automatically converted to dict)
await producer.send_result(result.submission_id, result)
```

## Migration Notes

### Changes Made

1. **Created `models.py`**: Contains all Pydantic models
2. **Updated `kafka_client.py`**: 
   - Consumer validates messages with `SubmissionMessage`
   - Producer accepts `ResultMessage` instead of dict
3. **Updated `main.py`**:
   - `process_submission()` now accepts `SubmissionMessage`
   - Results are created as `ResultMessage` instances
4. **Updated `requirements.txt`**: Added `pydantic==2.5.0`

### Breaking Changes

None - the Kafka message format remains the same. Only the internal handling changed.

## Testing

To test the new models:

```python
from models import SubmissionMessage, ResultMessage

# Valid submission
try:
    submission = SubmissionMessage(
        submission_id=1,
        task_id=5,
        user_id=42,
        code="print('hello')",
        language_id=50
    )
    print("Valid!")
except ValidationError as e:
    print(f"Invalid: {e}")

# Invalid submission (missing required fields)
try:
    submission = SubmissionMessage(
        submission_id=1
    )
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## Future Enhancements

Potential improvements:
- Add custom validators for code syntax checking
- Add message versioning support
- Create separate models for different language submissions
- Add detailed test result models
- Implement message schema evolution

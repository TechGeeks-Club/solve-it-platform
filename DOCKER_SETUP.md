# Solve-IT Platform - Microservices Architecture

Complete Docker-based setup with Django, Judge0, Kafka, and Nginx.

## Architecture Overview

```
┌─────────────┐
│   Nginx     │ ← Port 80 (Reverse Proxy)
└──────┬──────┘
       │
       ├──→ Static/Media Files
       │
       └──→ ┌──────────────┐
            │   Django     │ ← Port 8000
            │  Application │
            └──────┬───────┘
                   │
                   ├──→ SQLite Database
                   │
                   └──→ ┌────────────┐
                        │   Kafka    │ ← Port 9092/9093
                        └─────┬──────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼────────┐  ┌──────▼───────────┐
            │ Judge Service  │  │  Django Producer │
            │ (Microservice) │  │  (Future)        │
            └───────┬────────┘  └──────────────────┘
                    │
                    ├──→ ┌──────────────┐
                    │    │   Judge0     │ ← Port 2358
                    │    │   Server     │
                    │    └──────────────┘
                    │
                    └──→ ┌──────────────┐
                         │    Redis     │
                         └──────────────┘
```

## Services

1. **Django Application** - Main web application
2. **Judge0 Server** - Code execution engine
3. **Judge0 Worker** - Processes code submissions
4. **Judge Microservice** - Kafka consumer that handles Judge0 integration
5. **Kafka** - Message broker for async communication
6. **Zookeeper** - Kafka coordination service
7. **Redis** - Cache and Judge0 queue
8. **Nginx** - Reverse proxy and static file server
9. **PostgreSQL** - Optional database (currently using SQLite)

## Prerequisites

- Docker (>= 20.10)
- Docker Compose (>= 2.0)

## Quick Start

### 1. Clone and Setup

```bash
cd /home/amar/solve-it-platform
cp .env.example .env
# Edit .env with your configuration
```

### 2. Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Initialize Django

```bash
# Run migrations
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createsuperuser

# Collect static files (already done in startup)
docker-compose exec django python manage.py collectstatic --noinput
```

### 4. Access the Application

- **Web Application**: http://localhost
- **Django Admin**: http://localhost/admin
- **Judge0 API**: http://localhost:2358 (internal)

## Service Management

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Restart Specific Service
```bash
docker-compose restart django
docker-compose restart judge-microservice
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f django
docker-compose logs -f judge-microservice
docker-compose logs -f judge0-server
```

### Rebuild After Code Changes
```bash
# Rebuild specific service
docker-compose build django
docker-compose up -d django

# Rebuild all
docker-compose build
docker-compose up -d
```

## Database Management

### Using SQLite (Default)

The database file is located at `/home/amar/solve-it-platform/src/db.sqlite3`

```bash
# Backup database
docker-compose exec django python manage.py dumpdata > backup.json

# Restore database
docker-compose exec django python manage.py loaddata backup.json
```

### Switch to PostgreSQL (Optional)

1. Update `.env`:
```env
DATABASE_URL=postgresql://solveit:solveit123@db:5432/solveitdb
```

2. Update `settings.py` to use DATABASE_URL:
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}
```

3. Add to requirements.txt:
```
dj-database-url==2.1.0
```

## Judge0 Configuration

### Supported Languages

Judge0 supports 60+ languages. Common language IDs:

- **C (GCC 9.2.0)**: 50
- **C++ (GCC 9.2.0)**: 54
- **Python (3.8.1)**: 71
- **Java (OpenJDK 13.0.1)**: 62
- **JavaScript (Node.js 12.14.0)**: 63

Full list: http://localhost:2358/languages

### Test Judge0

```bash
# Check Judge0 status
curl http://localhost:2358/about

# Submit a test
curl -X POST http://localhost:2358/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "#include <stdio.h>\nint main() { printf(\"Hello World\"); return 0; }",
    "language_id": 50,
    "stdin": ""
  }'
```

## Kafka Topics

- **code-submissions**: Submissions sent from Django
- **code-results**: Results sent back from Judge microservice

### Monitor Kafka

```bash
# List topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# View messages in submission topic
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic code-submissions \
  --from-beginning
```

## Development

### Hot Reload

Django will auto-reload on code changes since the source is mounted as a volume.

```yaml
volumes:
  - ./src:/app  # Source code mounted for hot reload
```

### Debug Mode

Enable debug in `.env`:
```env
DEBUG=True
```

### Run Django Commands

```bash
docker-compose exec django python manage.py <command>

# Examples:
docker-compose exec django python manage.py shell
docker-compose exec django python manage.py makemigrations
docker-compose exec django python manage.py migrate
```

## Production Deployment

### Security Checklist

1. ✅ Change `DJANGO_SECRET_KEY` in `.env`
2. ✅ Set `DEBUG=False` in `.env`
3. ✅ Update `ALLOWED_HOSTS` with your domain
4. ✅ Change all default passwords
5. ✅ Use PostgreSQL instead of SQLite
6. ✅ Enable HTTPS in Nginx
7. ✅ Set up proper firewall rules
8. ✅ Configure backup strategy

### SSL/HTTPS Setup

1. Get SSL certificates (Let's Encrypt recommended)
2. Update `nginx/conf.d/default.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of config
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
docker-compose ps

# Check logs for errors
docker-compose logs <service-name>

# Remove and recreate
docker-compose down -v
docker-compose up -d
```

### Database Locked (SQLite)

SQLite doesn't handle concurrent writes well. Consider switching to PostgreSQL for production.

### Judge0 Not Responding

```bash
# Check Judge0 health
docker-compose logs judge0-server
docker-compose logs judge0-worker

# Restart Judge0
docker-compose restart judge0-server judge0-worker
```

### Kafka Connection Issues

```bash
# Check if Kafka is running
docker-compose ps kafka zookeeper

# Check Kafka logs
docker-compose logs kafka

# Recreate Kafka
docker-compose stop kafka zookeeper
docker-compose rm -f kafka zookeeper
docker-compose up -d kafka zookeeper
```

## File Structure

```
solve-it-platform/
├── docker-compose.yml          # Main orchestration file
├── .env                        # Environment variables
├── .env.example               # Environment template
├── src/                       # Django application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── judge-microservice/        # Judge0 integration service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── judge_service.py
├── nginx/                     # Nginx configuration
│   ├── nginx.conf
│   └── conf.d/
│       └── default.conf
└── judge0/                    # Judge0 configuration
    └── judge0.conf
```

## Monitoring

### Resource Usage

```bash
# Check container resources
docker stats

# Check disk usage
docker system df
```

### Health Checks

All services have health checks defined in docker-compose.yml.

```bash
# Check health status
docker-compose ps
```

## Backup & Restore

### Backup Everything

```bash
# Backup database
docker-compose exec django python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz src/media/

# Backup volumes
docker run --rm -v solve-it-platform_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data
```

## Next Steps

1. **Integrate Kafka Producer in Django**: Update `tasks/views.py` to send submissions to Kafka
2. **Add Kafka Consumer in Django**: Listen to results and update TaskSolution models
3. **Add Authentication**: Secure the Judge0 API if exposed
4. **Add Monitoring**: Set up Prometheus + Grafana
5. **Add CI/CD**: GitHub Actions for automated deployment

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review configuration in `.env`
- Ensure all services are healthy: `docker-compose ps`

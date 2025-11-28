#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
until python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        dbname="${POSTGRES_DB}",
        user="${POSTGRES_USER}",
        password="${POSTGRES_PASSWORD}",
        host="${DB_HOST}",
        port="${DB_PORT}"
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - continuing..."

# Make migrations for any model changes
echo "Creating migrations..."
python manage.py makemigrations --noinput

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Load initial data if database is empty
echo "Checking if initial data needs to be loaded..."
python << END
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
django.setup()

from tasks.models import Phase, Task

# Check if database is empty
if not Phase.objects.exists() and not Task.objects.exists():
    print("Database is empty. Loading initial data...")
    import subprocess
    result = subprocess.run(
        ['python', 'manage.py', 'loaddata', '/app/database/json_db/init_data.json'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("Initial data loaded successfully!")
    else:
        print(f"Error loading initial data: {result.stderr}")
else:
    print("Database already contains data. Skipping initial data load.")
END

echo "Starting application..."
exec "$@"

#!/bin/bash

# Solve-IT Platform - Quick Start Script
# Exit script if an error occurs
set -e
# Print trace of commands
set -x

echo "🚀 Starting Solve-IT Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before proceeding."
    exit 1
fi

# Build services
echo "🔨 Building Docker images..."
docker compose build

# Start services
echo "▶️  Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if Django is ready
echo "🔍 Checking Django service..."
until docker compose exec -T django python manage.py check > /dev/null 2>&1; do
    echo "   Waiting for Django..."
    sleep 3
done

# Run migrations
echo "📊 Running database migrations..."
docker compose exec -T django python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
docker compose exec -T django python manage.py collectstatic --noinput

echo ""
echo "✅ Solve-IT Platform is running!"
echo ""
echo "🌐 Access the application:"
echo "   Web: http://localhost"
echo "   Admin: http://localhost/admin"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker compose logs -f"
echo "   Stop: docker compose down"
echo "   Restart: docker compose restart"
echo ""
echo "📖 For more information, see DOCKER_SETUP.md"

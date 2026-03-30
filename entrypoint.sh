#!/bin/bash

set -e

echo "Starting entrypoint script..."

# On Railway, DATABASE_URL is provided directly
# On local Docker, we wait for 'db' service
if [ -n "$DATABASE_URL" ]; then
    echo "Railway environment detected, using DATABASE_URL..."
    # Extract host using Python (more reliable than sed)
    DB_HOST=$(python3 -c "import urllib.parse, os; u=urllib.parse.urlparse(os.environ['DATABASE_URL']); print(u.hostname)")
    DB_PORT=$(python3 -c "import urllib.parse, os; u=urllib.parse.urlparse(os.environ['DATABASE_URL']); print(u.port or 5432)")
else
    echo "Local environment detected..."
    DB_HOST=${PGHOST:-db}
    DB_PORT=${PGPORT:-5432}
fi

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

until nc -z "$DB_HOST" "$DB_PORT"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done

echo "PostgreSQL is up - continuing..."
sleep 2

echo "Running database migrations..."
python manage.py migrate --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser..."
    python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created')
else:
    print('Superuser already exists')
EOF
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Static files collection skipped"

echo "Entrypoint completed. Starting application..."
exec "$@"

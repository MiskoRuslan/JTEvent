.PHONY: help build up down restart logs shell migrate makemigrations superuser test clean

help:
	@echo "Available commands:"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs (all services)"
	@echo "  make logs-web       - View web service logs"
	@echo "  make logs-celery    - View celery service logs"
	@echo "  make shell          - Access Django shell"
	@echo "  make bash           - Access container bash"
	@echo "  make migrate        - Run migrations"
	@echo "  make makemigrations - Create migrations"
	@echo "  make superuser      - Create superuser"
	@echo "  make collectstatic  - Collect static files"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Stop and remove containers, volumes"
	@echo "  make prod-up        - Start with production settings"
	@echo "  make prod-down      - Stop production services"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-celery:
	docker-compose logs -f celery

shell:
	docker-compose exec web python manage.py shell

bash:
	docker-compose exec web bash

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

superuser:
	docker-compose exec web python manage.py createsuperuser

collectstatic:
	docker-compose exec web python manage.py collectstatic --noinput

test:
	docker-compose exec web python manage.py test

clean:
	docker-compose down -v
	docker system prune -f

# Production commands
prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

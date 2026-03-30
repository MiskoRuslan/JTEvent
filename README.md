# JTEvent (Join To Event)

Event management platform built with Django REST Framework and Alpine.js. Create, discover, and manage events with modern UI and real-time notifications.

## Features

### Authentication & Users
- Google OAuth 2.0 integration with one-click sign-in
- JWT-based authentication
- User profiles with dashboard

### Event Management
- Create and manage events with rich details (title, description, location, date, capacity)
- 12 event categories (Conference, Workshop, Music, Sports, Tech, Art, Food, Networking, Education, Charity, Gaming, Other)
- Default category-based banners when no cover image uploaded
- Event search and filtering
- Registration system with capacity limits and waitlist support
- Automatic status management (confirmed, waitlist, cancelled)

### Notifications
- Email confirmation on event registration (Ukrainian language)
- ICS calendar file attachment for easy calendar integration
- Asynchronous email delivery via Celery

### UI/UX
- Dark mode by default with light mode toggle
- Responsive design with Tailwind CSS
- Custom dropdowns and interactive components with Alpine.js
- Glass-morphism effects and gradient accents
- Mobile-friendly interface

### Technical Stack
- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL 16
- **Cache & Queue**: Redis, Celery
- **Frontend**: Alpine.js, Tailwind CSS
- **Deployment**: Docker, Docker Compose

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Gmail account with App Password (for email functionality)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd JTEvent
```

2. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and set:
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (from Google Cloud Console)
- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` (Gmail App Password)
- `SECRET_KEY` (generate new Django secret key)

3. **Start containers**
```bash
docker-compose up -d
```

4. **Run migrations**
```bash
docker-compose exec web python manage.py migrate
```

5. **Create superuser (optional)**
```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Access the application**
- Frontend: http://localhost:8000
- Admin panel: http://localhost:8000/admin
- API docs: http://localhost:8000/api/

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Login with email/password
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/google/` - Google OAuth login
- `POST /api/auth/token/refresh/` - Refresh JWT token

### Events
- `GET /api/events/` - List all events
- `POST /api/events/` - Create event (authenticated)
- `GET /api/events/{id}/` - Get event details
- `PUT /api/events/{id}/` - Update event (owner only)
- `DELETE /api/events/{id}/` - Delete event (owner only)
- `POST /api/events/{id}/register/` - Register for event
- `POST /api/events/{id}/cancel/` - Cancel registration

### Registrations
- `GET /api/registrations/my_registrations/` - User's registrations

## Project Structure

```
JTEvent/
├── event_management/       # Django project settings
│   ├── settings/
│   │   ├── base.py        # Base settings
│   │   ├── development.py # Development settings
│   │   └── production.py  # Production settings
│   ├── wsgi.py
│   └── urls.py
├── users/                 # User authentication app
│   ├── models.py         # Custom User model
│   ├── views.py          # Auth views (Google OAuth)
│   └── serializers.py
├── events/               # Events management app
│   ├── models.py        # Event, EventRegistration models
│   ├── views.py         # Event ViewSets
│   ├── serializers.py   # Event serializers
│   └── tasks.py         # Celery tasks (email sending)
├── templates/           # HTML templates
│   ├── base.html       # Base template with theme
│   ├── auth/           # Login, register pages
│   ├── events/         # Event pages
│   ├── profile/        # Dashboard
│   └── emails/         # Email templates
├── static/             # Static files
│   ├── js/app.js      # Alpine.js components & API client
│   ├── css/           # Tailwind CSS
│   └── banners/       # Category default banners
├── docker-compose.yml  # Docker services configuration
├── Dockerfile         # Django container
└── requirements.txt   # Python dependencies
```

## Development

### View logs
```bash
docker-compose logs -f web      # Django logs
docker-compose logs -f celery   # Celery worker logs
```

### Run tests
```bash
docker-compose exec web python manage.py test
```

### Django shell
```bash
docker-compose exec web python manage.py shell
```

### Rebuild containers
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Email Configuration

For production, configure SMTP settings in `.env`:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```

**Note**: Use Gmail App Password, not your regular password. Generate at: https://myaccount.google.com/apppasswords

## License

MIT License

## Support

For issues and feature requests, please open an issue on GitHub.

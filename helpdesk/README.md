# HelpDesk — Support Ticket System

A full-featured help desk built with Django, Bootstrap 5, and SQLite.

## Features

- Role-based access: Admin, Agent, User
- Full ticket lifecycle (Open → In Progress → Resolved → Closed)
- Comments with internal notes (agent-only)
- File attachments per ticket
- SLA deadline tracking and breach reporting
- Reports and analytics
- REST API (DRF)

## Quick Start

### 1. Set up the environment

```bash
cd helpdesk
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run migrations

```bash
python manage.py makemigrations accounts tickets
python manage.py migrate
```

### 3. Load initial data

```bash
python manage.py loaddata tickets/fixtures/initial_data.json
```

### 4. Create a superuser (Admin)

```bash
python manage.py createsuperuser
```

When prompted, set the role to `admin` via the Django admin panel after creation,
or use the shell:

```bash
python manage.py shell -c "from accounts.models import User; User.objects.filter(is_superuser=True).update(role='admin')"
```

### 5. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — you'll be redirected to the login page.

## Default URLs

| URL | Description |
|-----|-------------|
| `/login/` | Login |
| `/register/` | Register new user |
| `/dashboard/` | Dashboard |
| `/tickets/` | Ticket list |
| `/tickets/create/` | Create ticket |
| `/admin/users/` | User management (admin) |
| `/admin/categories/` | Category management (admin) |
| `/admin/sla/` | SLA rules (admin) |
| `/reports/` | Reports (admin/agent) |
| `/api/tickets/` | REST API |

## User Roles

| Role | Capabilities |
|------|-------------|
| `admin` | Full access: users, categories, SLA, all tickets |
| `agent` | View/update assigned tickets, internal notes, reports |
| `user` | Create tickets, comment, rate resolved tickets |

## Project Structure

```
helpdesk/
├── manage.py
├── helpdesk/           # Django project settings
├── accounts/           # Custom user model + auth views
├── tickets/            # Core ticket, comment, SLA, reports
├── templates/          # base.html
├── static/             # CSS, JS
└── media/              # Uploaded files
```

## Production Notes

- Set `DEBUG = False` and configure `SECRET_KEY` via environment variable
- Set `ALLOWED_HOSTS` to your domain
- Use a production database (PostgreSQL recommended)
- Configure a real email backend in settings
- Run `python manage.py collectstatic` before deployment

# Deployment Guide for HelpDesk Application

This guide covers deployment options for the Django HelpDesk application.

## Quick Start Options

### Option 1: Render (Recommended for beginners)

1. **Push code to GitHub**
2. **Create account at [render.com](https://render.com)**
3. **Create new Web Service**
   - Connect your GitHub repository
   - Choose Python environment
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn helpdesk.wsgi:application`
4. **Configure environment variables**:
   ```
   DEBUG=False
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=your-app.onrender.com
   DB_ENGINE=django.db.backends.postgresql
   ```
5. **Add PostgreSQL database** on Render
6. **Set up static files**: Add `python manage.py collectstatic --noinput` to build command

### Option 2: PythonAnywhere

1. **Create account at [pythonanywhere.com](https://pythonanywhere.com)**
2. **Upload files** via Git or manual upload
3. **Create virtual environment**:
   ```bash
   mkvirtualenv helpdesk --python=python3.11
   pip install -r requirements.txt
   ```
4. **Configure web app**:
   - WSGI configuration file: `/var/www/yourusername_pythonanywhere_com_wsgi.py`
   - Add:
     ```python
     import os
     import sys
     path = '/home/yourusername/helpdesk'
     if path not in sys.path:
         sys.path.append(path)
     os.environ['DJANGO_SETTINGS_MODULE'] = 'helpdesk.settings'
     from django.core.wsgi import get_wsgi_application
     application = get_wsgi_application()
     ```
5. **Set up static files** in web app configuration

### Option 3: Railway

1. **Install Railway CLI**: `npm i -g @railway/cli`
2. **Initialize project**: `railway init`
3. **Deploy**: `railway up`
4. **Add PostgreSQL plugin**
5. **Set environment variables** in Railway dashboard

## Environment Variables Setup

Create a `.env` file in production (use `.env.example` as template):

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-secure-secret-key-here
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=helpdesk_db
DB_USER=helpdesk_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=helpdesk@your-domain.com
```

## Production Setup Steps

### 1. Database Migration

```bash
# For PostgreSQL
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 2. Static Files Collection

```bash
python manage.py collectstatic --noinput
```

### 3. Load Initial Data (Optional)

```bash
python manage.py loaddata tickets/fixtures/initial_data.json
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t helpdesk-app .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f web
```

### Docker Commands

```bash
# Stop containers
docker-compose down

# Rebuild images
docker-compose build --no-cache

# Access database
docker-compose exec db psql -U helpdesk_user -d helpdesk_db
```

## Nginx Configuration (For Self-Hosting)

If deploying on your own server, configure Nginx:

1. **Install Nginx**:
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. **Create Nginx config** at `/etc/nginx/sites-available/helpdesk`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location /static/ {
           alias /path/to/helpdesk/staticfiles/;
       }
       
       location /media/ {
           alias /path/to/helpdesk/media/;
       }
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

3. **Enable site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/helpdesk /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## SSL/HTTPS Configuration

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Monitoring and Maintenance

### 1. **Backup Database**
```bash
# PostgreSQL backup
pg_dump -U helpdesk_user helpdesk_db > backup_$(date +%Y%m%d).sql
```

### 2. **Check Logs**
```bash
# Application logs
tail -f django_errors.log

# System logs
sudo journalctl -u gunicorn -f
```

### 3. **Update Dependencies**
```bash
pip install -r requirements.txt --upgrade
python manage.py migrate
python manage.py collectstatic --noinput
```

## Troubleshooting

### Common Issues:

1. **Static files not loading**:
   - Run `python manage.py collectstatic`
   - Check Nginx/Apache configuration
   - Verify file permissions

2. **Database connection errors**:
   - Check environment variables
   - Verify PostgreSQL is running
   - Check firewall settings

3. **CSRF verification failed**:
   - Ensure `CSRF_COOKIE_SECURE = True` with HTTPS
   - Check `ALLOWED_HOSTS` configuration

4. **Email not sending**:
   - Verify SMTP credentials
   - Check email backend configuration
   - Test with `python manage.py sendtestemail`

## Support

For deployment issues:
1. Check logs: `docker-compose logs` or application logs
2. Verify environment variables
3. Ensure database migrations are applied
4. Check static file permissions

Remember to always backup your database before making significant changes!
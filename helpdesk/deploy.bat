@echo off
REM HelpDesk Deployment Script for Windows
REM Usage: deploy.bat [production|staging]

setlocal enabledelayedexpansion

set ENVIRONMENT=%~1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

echo 🚀 Deploying HelpDesk application (%ENVIRONMENT% environment)

REM Check Python version
echo 📋 Checking Python version...
python --version
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+.
    exit /b 1
)

REM Create/activate virtual environment
set VENV_DIR=venv
if not exist "%VENV_DIR%" (
    echo 🔧 Creating virtual environment...
    python -m venv %VENV_DIR%
)

echo 🔧 Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat

REM Install/upgrade dependencies
echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Run database migrations
echo 🔄 Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create superuser if not exists
echo 👤 Checking for superuser...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exists = User.objects.filter(is_superuser=True).exists(); print('True' if exists else 'False')" > temp.txt
set /p SUPERUSER_EXISTS=<temp.txt
del temp.txt

if "%SUPERUSER_EXISTS%"=="False" (
    echo 👑 Creating superuser...
    python manage.py createsuperuser
) else (
    echo ✅ Superuser already exists
)

REM Load initial data if exists
if exist "tickets\fixtures\initial_data.json" (
    echo 📊 Loading initial data...
    python manage.py loaddata tickets\fixtures\initial_data.json
)

REM Collect static files for production
if "%ENVIRONMENT%"=="production" (
    echo 📁 Collecting static files...
    python manage.py collectstatic --noinput
    
    echo 🔒 Setting production security settings...
    REM Check if production settings exist
    if exist "helpdesk\settings_production.py" (
        echo ⚠️  Using production settings. Please configure environment variables!
    )
)

REM Run tests
echo 🧪 Running tests...
python manage.py test --failfast

echo ✅ Deployment preparation complete!

if "%ENVIRONMENT%"=="development" (
    echo.
    echo 🎮 To start development server:
    echo    python manage.py runserver
    echo.
    echo 📱 Development URL: http://127.0.0.1:8000
) else if "%ENVIRONMENT%"=="production" (
    echo.
    echo 🚀 Production deployment ready!
    echo.
    echo To deploy with Gunicorn:
    echo    gunicorn helpdesk.wsgi:application --bind 0.0.0.0:8000
    echo.
    echo For Docker deployment:
    echo    docker-compose up -d
)

echo.
echo 📝 Next steps:
echo 1. Configure environment variables in .env file
echo 2. Set up production database (PostgreSQL recommended)
echo 3. Configure email settings
echo 4. Set up SSL/HTTPS
echo 5. Configure backup strategy

pause
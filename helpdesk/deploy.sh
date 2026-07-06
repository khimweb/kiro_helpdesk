#!/bin/bash

# HelpDesk Deployment Script
# Usage: ./deploy.sh [production|staging]

set -e  # Exit on error

ENVIRONMENT=${1:-production}
VENV_DIR="venv"
REQUIREMENTS="requirements.txt"
SETTINGS_FILE="helpdesk/settings.py"

echo "🚀 Deploying HelpDesk application ($ENVIRONMENT environment)"

# Check Python version
echo "📋 Checking Python version..."
python --version

# Create/activate virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 Creating virtual environment..."
    python -m venv $VENV_DIR
fi

echo "🔧 Activating virtual environment..."
source $VENV_DIR/bin/activate  # For Linux/Mac
# On Windows (Git Bash): source $VENV_DIR/Scripts/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r $REQUIREMENTS

# Run database migrations
echo "🔄 Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if not exists
echo "👤 Checking for superuser..."
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
    echo "👑 Creating superuser..."
    python manage.py createsuperuser
else
    echo "✅ Superuser already exists"
fi

# Load initial data if exists
if [ -f "tickets/fixtures/initial_data.json" ]; then
    echo "📊 Loading initial data..."
    python manage.py loaddata tickets/fixtures/initial_data.json
fi

# Collect static files for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput
    
    echo "🔒 Setting production security settings..."
    # Check if production settings exist
    if [ -f "helpdesk/settings_production.py" ]; then
        echo "⚠️  Using production settings. Please configure environment variables!"
    fi
fi

# Run tests
echo "🧪 Running tests..."
python manage.py test --failfast

echo "✅ Deployment preparation complete!"

if [ "$ENVIRONMENT" = "development" ]; then
    echo ""
    echo "🎮 To start development server:"
    echo "   python manage.py runserver"
    echo ""
    echo "📱 Development URL: http://127.0.0.1:8000"
elif [ "$ENVIRONMENT" = "production" ]; then
    echo ""
    echo "🚀 Production deployment ready!"
    echo ""
    echo "To deploy with Gunicorn:"
    echo "   gunicorn helpdesk.wsgi:application --bind 0.0.0.0:8000"
    echo ""
    echo "For Docker deployment:"
    echo "   docker-compose up -d"
fi

echo ""
echo "📝 Next steps:"
echo "1. Configure environment variables in .env file"
echo "2. Set up production database (PostgreSQL recommended)"
echo "3. Configure email settings"
echo "4. Set up SSL/HTTPS"
echo "5. Configure backup strategy"
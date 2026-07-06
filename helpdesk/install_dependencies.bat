@echo off
echo Installing HelpDesk Dependencies...
echo ====================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Python found, checking virtual environment...

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    echo.
    echo You can try installing manually:
    echo 1. Activate virtual environment: venv\Scripts\activate
    echo 2. Install dependencies one by one:
    echo    pip install Django==4.2.7
    echo    pip install djangorestframework==3.14.0
    echo    pip install Pillow==10.4.0
    echo    pip install django-crispy-forms==2.1
    echo    pip install crispy-bootstrap5==0.7
    echo    pip install django-filter==23.3
    echo    pip install requests==2.31.0
    pause
    exit /b 1
)

echo.
echo ====================================
echo All dependencies installed successfully!
echo.
echo To run the development server:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Run migrations: python manage.py migrate
echo 3. Create superuser: python manage.py createsuperuser
echo 4. Run server: python manage.py runserver
echo.
echo The server will be available at: http://127.0.0.1:8000
echo ====================================
pause
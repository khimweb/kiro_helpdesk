# Installing Missing Dependencies

## Error Solution
The error `ModuleNotFoundError: No module named 'requests'` occurs because the `requests` library is not installed.

## Installation Methods

### Method 1: Install using pip (Recommended)
```bash
# Activate your virtual environment first (if using one)
# On Windows:
cd helpdesk
venv\Scripts\activate

# Install requests
pip install requests==2.31.0
```

### Method 2: Install all dependencies from requirements.txt
```bash
cd helpdesk
pip install -r requirements.txt
```

### Method 3: If using a virtual environment
```bash
# Windows
cd helpdesk
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Linux/Mac
cd helpdesk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## What is 'requests'?
The `requests` library is used for making HTTP requests to external APIs. In this project, it's used to:
- Send notifications to Telegram bots
- Make API calls to Telegram's Bot API
- Handle web communication

## Alternative Solution (Development Only)
If you just want to run the application without Telegram notifications temporarily, the system will still work. The notifications module has been updated to handle the missing `requests` module gracefully. You'll see warnings in the console but the application will continue to function.

## Verification
After installation, you can verify with:
```bash
python -c "import requests; print('requests version:', requests.__version__)"
```

Expected output: `requests version: 2.31.0`

## Notes
- The `requests` module is lightweight and widely used
- It's already included in the `requirements.txt` file
- The application handles missing `requests` gracefully (will show warnings but won't crash)
- iOS-style notifications will still work even without `requests` (only Telegram alerts will be affected)
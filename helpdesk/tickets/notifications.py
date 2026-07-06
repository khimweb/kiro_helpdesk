"""
Notifications module for sending Telegram bot alerts and displaying iOS-style notifications
"""

import json
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model

# Try to import requests, but handle if it's not installed
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' module not installed. Telegram notifications will not work.")
    print("Install it with: pip install requests")

# Telegram Bot Tokens
TELEGRAM_TOKENS = {
    'changes': '8927476132:AAHq009I9fT1J96LM2BGqFfL2W7Mxm8nLGc',  # changeeverthingalert_bot
    'system_info': '8845871042:AAFe2LSpwvRRSdQpFPilgQqDCDIWJjqIoGE',  # Allnewsofsystem_bot
    'auth': '8565862986:AAFjuzGRnndJEcpm3TNmhHhB0fl_Y5-28Fk',  # loginorsignininformation_bot
}

# Telegram Bot URLs
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

def send_telegram_alert(bot_type, message, chat_id=None):
    """
    Send alert to Telegram bot
    
    Args:
        bot_type: 'changes', 'system_info', or 'auth'
        message: Message to send
        chat_id: Optional chat ID (uses default if not provided)
    """
    # Check if requests module is available
    if not REQUESTS_AVAILABLE:
        print(f"Telegram alert not sent: 'requests' module not installed")
        print(f"Bot: {bot_type}, Message: {message[:100]}...")
        return False
    
    try:
        token = TELEGRAM_TOKENS.get(bot_type)
        if not token:
            print(f"Error: Invalid bot type '{bot_type}'")
            return False
        
        # For simplicity, we'll send to the bot itself (can be configured)
        # In production, you'd want to store chat IDs in database
        if not chat_id:
            # Default chat ID (bot's own chat)
            chat_id = get_default_chat_id(bot_type)
        
        url = TELEGRAM_API_URL.format(token=token)
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")
        return False

def get_default_chat_id(bot_type):
    """Get default chat ID for each bot type"""
    # These are example chat IDs - in production, store in settings or database
    default_chat_ids = {
        'changes': '1294502034',  # Your user ID
        'system_info': '1294502034',
        'auth': '1294502034'
    }
    return default_chat_ids.get(bot_type, '1294502034')

def send_change_alert(user, action, object_type, object_info, details=None):
    """
    Send change alert to Telegram
    
    Args:
        user: User object performing the action
        action: 'create', 'update', 'delete', 'edit'
        object_type: 'ticket', 'category', 'user', etc.
        object_info: Information about the object
        details: Additional details
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"""
🔄 <b>Change Alert</b>
━━━━━━━━━━━━━━━━━━━━
👤 <b>User:</b> {user.username} ({user.email})
🎯 <b>Action:</b> {action.upper()}
📋 <b>Type:</b> {object_type}
📝 <b>Info:</b> {object_info}
⏰ <b>Time:</b> {timestamp}
"""
    
    if details:
        message += f"📄 <b>Details:</b> {details}\n"
    
    return send_telegram_alert('changes', message)

def send_system_info_alert(user_info, action, details=None):
    """
    Send system information alert
    
    Args:
        user_info: User information string
        action: Action performed
        details: Additional details
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"""
📊 <b>System Information</b>
━━━━━━━━━━━━━━━━━━━━
👤 <b>User Info:</b> {user_info}
⚡ <b>Action:</b> {action}
⏰ <b>Time:</b> {timestamp}
"""
    
    if details:
        message += f"📄 <b>Details:</b> {details}\n"
    
    return send_telegram_alert('system_info', message)

def send_auth_alert(username, action, success, ip_address=None, details=None):
    """
    Send authentication alert (login/signup)
    
    Args:
        username: Username attempting auth
        action: 'login' or 'signup'
        success: True if successful, False if failed
        ip_address: User's IP address
        details: Additional details (error message, etc.)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "✅ SUCCESS" if success else "❌ FAILED"
    
    message = f"""
🔐 <b>Authentication Alert</b>
━━━━━━━━━━━━━━━━━━━━
👤 <b>Username:</b> {username}
📱 <b>Action:</b> {action.upper()}
📊 <b>Status:</b> {status}
⏰ <b>Time:</b> {timestamp}
"""
    
    if ip_address:
        message += f"🌐 <b>IP Address:</b> {ip_address}\n"
    
    if details:
        message += f"📄 <b>Details:</b> {details}\n"
    
    return send_telegram_alert('auth', message)

# iOS-style notification templates for frontend
IOS_NOTIFICATION_TEMPLATES = {
    'success': {
        'title': 'Success',
        'icon': '✅',
        'color': '#4CAF50',
        'bg_color': '#E8F5E9'
    },
    'error': {
        'title': 'Error',
        'icon': '❌',
        'color': '#F44336',
        'bg_color': '#FFEBEE'
    },
    'info': {
        'title': 'Info',
        'icon': 'ℹ️',
        'color': '#2196F3',
        'bg_color': '#E3F2FD'
    },
    'warning': {
        'title': 'Warning',
        'icon': '⚠️',
        'color': '#FF9800',
        'bg_color': '#FFF3E0'
    },
    'change': {
        'title': 'Change Detected',
        'icon': '🔄',
        'color': '#9C27B0',
        'bg_color': '#F3E5F5'
    }
}

def get_ios_notification_data(notification_type, message, auto_hide=True, duration=4000):
    """
    Get iOS-style notification data for frontend
    
    Args:
        notification_type: 'success', 'error', 'info', 'warning', 'change'
        message: Notification message
        auto_hide: Whether to auto-hide notification
        duration: Duration in milliseconds (default: 4000ms = 4 seconds)
    
    Returns:
        dict with notification data
    """
    template = IOS_NOTIFICATION_TEMPLATES.get(notification_type, IOS_NOTIFICATION_TEMPLATES['info'])
    
    return {
        'type': notification_type,
        'title': template['title'],
        'icon': template['icon'],
        'message': message,
        'color': template['color'],
        'bg_color': template['bg_color'],
        'auto_hide': auto_hide,
        'duration': duration,
        'timestamp': datetime.now().isoformat()
    }
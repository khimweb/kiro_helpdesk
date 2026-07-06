"""
Telegram Notification Test
Use this to test if Telegram notifications are working
"""

import sys
import os

# Add the project to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helpdesk.settings')

import django
django.setup()

from tickets.notifications import (
    send_telegram_alert,
    send_change_alert,
    send_auth_alert,
    send_system_info_alert
)
from accounts.models import User

def test_telegram_alerts():
    """Test all Telegram alert functions"""
    print("=" * 60)
    print("Testing Telegram Notifications")
    print("=" * 60)
    
    # Test 1: Direct Telegram alert
    print("\n1. Testing direct Telegram alert...")
    result = send_telegram_alert(
        bot_type='changes',
        message='<b>Test Alert</b>\nThis is a test message from the HelpDesk system.'
    )
    print(f"   Result: {'✅ Success' if result else '❌ Failed'}")
    
    # Test 2: Change alert
    print("\n2. Testing change alert...")
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'role': 'regular_user'
            }
        )
        
        result = send_change_alert(
            user=user,
            action='test',
            object_type='test_object',
            object_info='Test Object Info',
            details='This is a test change alert'
        )
        print(f"   Result: {'✅ Success' if result else '❌ Failed'}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Auth alert
    print("\n3. Testing auth alert...")
    result = send_auth_alert(
        username='testuser',
        action='login',
        success=True,
        ip_address='192.168.1.100',
        details='Test login successful'
    )
    print(f"   Result: {'✅ Success' if result else '❌ Failed'}")
    
    # Test 4: System info alert
    print("\n4. Testing system info alert...")
    result = send_system_info_alert(
        user_info='Test User (test@example.com)',
        action='system_test',
        details='This is a system information test'
    )
    print(f"   Result: {'✅ Success' if result else '❌ Failed'}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    # Check if requests module is installed
    try:
        import requests
        print(f"\n✅ Requests module is installed (v{requests.__version__})")
    except ImportError:
        print("\n❌ Requests module is NOT installed")
        print("   Install with: pip install requests")
    
    return True

if __name__ == "__main__":
    test_telegram_alerts()
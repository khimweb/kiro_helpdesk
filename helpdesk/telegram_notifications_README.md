# Telegram Bot Notifications & iOS-Style Alerts

## Overview
This system integrates Telegram bot notifications with iOS-style alerts for the HelpDesk application. When users perform actions (create, update, delete, login, signup), notifications are sent to Telegram bots and iOS-style alerts appear on the website.

## Telegram Bots

### 1. @changeeverthingalert_bot
- **Token:** `8927476132:AAHq009I9fT1J96LM2BGqFfL2W7Mxm8nLGc`
- **Purpose:** Track changes, edits, and deletions
- **Triggers:** Ticket creation/update/deletion, Category creation/update/deletion, User profile updates

### 2. @Allnewsofsystem_bot
- **Token:** `8845871042:AAFe2LSpwvRRSdQpFPilgQqDCDIWJjqIoGE`
- **Purpose:** System information and user actions
- **Triggers:** User management actions, system events

### 3. @loginorsignininformation_bot
- **Token:** `8565862986:AAFjuzGRnndJEcpm3TNmhHhB0fl_Y5-28Fk`
- **Purpose:** Authentication alerts
- **Triggers:** Login success/failure, Signup success/failure, Logout

## iOS-Style Alerts

### Features
- **Smooth Animations:** iOS 26 latest version style animations
- **Duration:** 4 seconds (configurable)
- **Auto-hide:** Automatically disappears after duration
- **Manual Close:** Click close button to dismiss immediately
- **Responsive:** Works on all screen sizes
- **Dark Mode:** Automatically adapts to system theme
- **Queue System:** Multiple notifications are queued and shown sequentially

### Notification Types
1. **Success (Green)**
   - Icon: ✅
   - Used for: Successful operations, creations, updates

2. **Error (Red)**
   - Icon: ❌
   - Used for: Failed operations, errors, validation failures

3. **Info (Blue)**
   - Icon: ℹ️
   - Used for: Information messages, general updates

4. **Warning (Orange)**
   - Icon: ⚠️
   - Used for: Warnings, confirmations required

5. **Change (Purple)**
   - Icon: 🔄
   - Used for: Change detections, modifications

## Implementation

### Backend (Python/Django)
The notification system is implemented in:
- `tickets/notifications.py` - Core notification functions
- `tickets/views.py` - Updated views to trigger notifications
- `accounts/views.py` - Updated authentication views

### Frontend (JavaScript/CSS)
- `static/js/ios-notifications.js` - iOS-style notification system
- `static/css/style.css` - Additional styles for notifications
- `templates/base.html` - Includes notification system

### How to Use

#### 1. Sending Telegram Alerts
```python
from tickets.notifications import send_change_alert

send_change_alert(
    user=request.user,
    action='create',  # create, update, delete, edit
    object_type='ticket',
    object_info='Ticket #123: Network Issue',
    details='Priority: High, Category: Network'
)
```

#### 2. Sending Authentication Alerts
```python
from tickets.notifications import send_auth_alert

send_auth_alert(
    username='john_doe',
    action='login',  # login, signup, logout
    success=True,
    ip_address='192.168.1.100',
    details='Successful authentication'
)
```

#### 3. Showing iOS Alerts (Frontend)
```javascript
// Using the global instance
window.IOSNotifications.success('Title', 'Message', 4000);

// Or using helper functions
window.IOSNotifications.success('Success', 'Operation completed', 4000);
window.IOSNotifications.error('Error', 'Something went wrong', 4000);
window.IOSNotifications.info('Info', 'Check your settings', 4000);
window.IOSNotifications.warning('Warning', 'Action required', 4000);
window.IOSNotifications.change('Change', 'Settings updated', 4000);
```

#### 4. From Django Template (Session)
```python
# In your view
request.session['ios_notification'] = {
    'type': 'success',
    'title': 'Ticket Created',
    'message': f'Ticket #{ticket.ticket_id} created successfully',
    'icon': '✅',
    'auto_hide': True,
    'duration': 4000
}
```

## Trigger Points

### Ticket Operations
1. **Create Ticket** - Success notification + Telegram alert
2. **Update Ticket** - Success notification + Telegram alert (with status/assignment changes)
3. **Delete Ticket** - Success notification + Telegram alert
4. **Add Comment** - Info notification (if configured)

### Category Operations (Admin only)
1. **Create Category** - Success notification + Telegram alert
2. **Update Category** - Success notification + Telegram alert
3. **Delete Category** - Success notification + Telegram alert

### User Operations
1. **User Registration** - Success/Error notification + Telegram alert
2. **User Login** - Success/Error notification + Telegram alert
3. **User Logout** - Info notification + Telegram alert
4. **Profile Update** - Success notification + Telegram alert
5. **User Management** (Admin) - Success notification + Telegram alert

## Testing

### Test Page
Access the notification test page at `/notifications-test/` (Admin only) to:
1. Test all notification types
2. See Telegram bot information
3. Verify notification features

### Manual Testing
1. Create a new ticket
2. Update an existing ticket
3. Delete a ticket
4. Register a new user
5. Login with correct/incorrect credentials
6. Update user profile

## Configuration

### Telegram Bot Settings
To change Telegram bot tokens, update `TELEGRAM_TOKENS` in `tickets/notifications.py`:
```python
TELEGRAM_TOKENS = {
    'changes': 'YOUR_CHANGE_BOT_TOKEN',
    'system_info': 'YOUR_SYSTEM_BOT_TOKEN',
    'auth': 'YOUR_AUTH_BOT_TOKEN',
}
```

### Notification Settings
Customize notification behavior in `tickets/notifications.py`:
- `IOS_NOTIFICATION_TEMPLATES` - Customize colors and icons
- `get_default_chat_id()` - Set default Telegram chat IDs
- `get_ios_notification_data()` - Customize notification defaults

### Styling
Customize iOS notification styles in `static/js/ios-notifications.js`:
- Animation durations
- Colors and themes
- Positioning and sizing
- Sound effects (if added)

## Security Notes

1. **Telegram Tokens:** Keep tokens secure in production
2. **IP Address:** User IP addresses are included in auth alerts
3. **Session Data:** Notification data is cleared from session after use
4. **Error Handling:** Failed Telegram sends are logged but don't break the app

## Troubleshooting

### Telegram Alerts Not Sending
1. Check internet connectivity
2. Verify Telegram bot tokens are correct
3. Check if Telegram API is accessible
4. Verify chat IDs are correct

### iOS Alerts Not Showing
1. Check browser console for errors
2. Verify JavaScript is loaded
3. Check if notification container is created
4. Verify session data is being passed correctly

### Notifications Too Frequent
1. Adjust notification triggers in views
2. Add conditional logic for minor changes
3. Implement notification throttling if needed

## Future Enhancements

1. **Database Logging:** Store notifications in database for audit
2. **User Preferences:** Allow users to customize notification settings
3. **Email Notifications:** Add email notifications alongside Telegram
4. **Mobile Push:** Implement push notifications for mobile
5. **Advanced Filtering:** Filter notifications by type/importance
6. **Sound Customization:** Allow custom notification sounds
7. **Notification History:** View past notifications in UI

## Support
For issues with the notification system:
1. Check the Telegram bot status
2. Review Django error logs
3. Test with the notification test page
4. Check browser console for JavaScript errors

---

**Note:** This system requires internet connectivity for Telegram alerts. If the Telegram API is unreachable, notifications will fail silently but the application will continue to function normally.
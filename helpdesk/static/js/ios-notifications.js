/**
 * iOS-style Notification System
 * Simple, reliable notifications that appear for 4 seconds from the right side
 */

class IOSNotificationSystem {
    constructor() {
        console.log('iOS Notification System Initializing...');
        this.container = null;
        this.notificationQueue = [];
        this.isShowing = false;
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        console.log('iOS Notification System Initialized');
        // Create notification container
        this.createContainer();
        
        // Check for session notifications
        this.checkSessionNotifications();
        
        // Listen for custom notification events
        document.addEventListener('showIOSNotification', (e) => {
            console.log('Custom notification event received:', e.detail);
            this.show(e.detail);
        });
    }

    createContainer() {
        // Remove existing container if any
        const existingContainer = document.querySelector('.ios-notifications-container');
        if (existingContainer) {
            existingContainer.remove();
        }

        // Create new container
        this.container = document.createElement('div');
        this.container.className = 'ios-notifications-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 99999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 350px;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
        console.log('Notification container created');

        // Add full styles
        this.addStyles();
    }

    addStyles() {
        const styles = `
            .ios-notifications-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 350px;
                pointer-events: none;
            }

            .ios-notification {
                position: relative;
                background: white;
                border-radius: 14px;
                padding: 16px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                opacity: 0;
                transform: translateX(100px);
                transition: all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
                pointer-events: auto;
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                overflow: hidden;
            }

            .ios-notification.show {
                opacity: 1;
                transform: translateX(0);
            }

            .ios-notification.hide {
                opacity: 0;
                transform: translateX(100px);
            }

            .ios-notification::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--notification-color, #007AFF), transparent);
                border-radius: 14px 14px 0 0;
            }

            .ios-notification-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 8px;
            }

            .ios-notification-icon {
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                flex-shrink: 0;
            }

            .ios-notification-title {
                font-size: 15px;
                font-weight: 600;
                color: #000;
                flex: 1;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
            }

            .ios-notification-time {
                font-size: 12px;
                color: #8E8E93;
                font-weight: 400;
            }

            .ios-notification-message {
                font-size: 14px;
                line-height: 1.4;
                color: #3C3C43;
                margin-top: 4px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
            }

            .ios-notification-close {
                position: absolute;
                top: 12px;
                right: 12px;
                width: 24px;
                height: 24px;
                border-radius: 12px;
                background: rgba(0, 0, 0, 0.05);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                opacity: 0;
                transition: opacity 0.2s ease;
                color: #8E8E93;
                font-size: 14px;
                border: none;
                padding: 0;
            }

            .ios-notification:hover .ios-notification-close {
                opacity: 1;
            }

            .ios-notification-close:hover {
                background: rgba(0, 0, 0, 0.1);
                color: #000;
            }

            /* Notification Types */
            .ios-notification-success {
                --notification-color: #34C759;
                background: rgba(52, 199, 89, 0.95);
            }

            .ios-notification-error {
                --notification-color: #FF3B30;
                background: rgba(255, 59, 48, 0.95);
            }

            .ios-notification-info {
                --notification-color: #007AFF;
                background: rgba(0, 122, 255, 0.95);
            }

            .ios-notification-warning {
                --notification-color: #FF9500;
                background: rgba(255, 149, 0, 0.95);
            }

            .ios-notification-change {
                --notification-color: #AF52DE;
                background: rgba(175, 82, 222, 0.95);
            }

            /* Dark mode support */
            @media (prefers-color-scheme: dark) {
                .ios-notification {
                    background: rgba(28, 28, 30, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }

                .ios-notification-title {
                    color: #FFF;
                }

                .ios-notification-message {
                    color: #EBEBF5;
                }

                .ios-notification-close {
                    background: rgba(255, 255, 255, 0.1);
                    color: #EBEBF5;
                }

                .ios-notification-close:hover {
                    background: rgba(255, 255, 255, 0.2);
                    color: #FFF;
                }
            }

            /* Responsive */
            @media (max-width: 768px) {
                .ios-notifications-container {
                    top: 10px;
                    right: 10px;
                    left: 10px;
                    max-width: none;
                }

                .ios-notification {
                    max-width: 100%;
                }
            }

            /* Animation keyframes */
            @keyframes slideInRight {
                from {
                    transform: translateX(100px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100px);
                    opacity: 0;
                }
            }

            @keyframes pulse {
                0%, 100% {
                    transform: scale(1);
                }
                50% {
                    transform: scale(1.05);
                }
            }

            .ios-notification-pulse {
                animation: pulse 0.3s ease;
            }
        `;

        const styleElement = document.createElement('style');
        styleElement.textContent = styles;
        document.head.appendChild(styleElement);
    }

    show(notificationData) {
        // Add to queue
        this.notificationQueue.push(notificationData);
        
        // Show next notification if not currently showing
        if (!this.isShowing) {
            this.showNext();
        }
    }

    showNext() {
        if (this.notificationQueue.length === 0) {
            this.isShowing = false;
            return;
        }

        this.isShowing = true;
        const notificationData = this.notificationQueue.shift();
        this.createAndShowNotification(notificationData);
    }

    createAndShowNotification(data) {
        const {
            type = 'info',
            title = 'Notification',
            icon = 'ℹ️',
            message = '',
            color,
            bg_color,
            auto_hide = true,
            duration = 4000,
            timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        } = data;

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `ios-notification ios-notification-${type}`;
        
        if (color) {
            notification.style.setProperty('--notification-color', color);
        }
        if (bg_color) {
            notification.style.background = bg_color;
        }

        notification.innerHTML = `
            <div class="ios-notification-header">
                <div class="ios-notification-icon">${icon}</div>
                <div class="ios-notification-title">${title}</div>
                <div class="ios-notification-time">${timestamp}</div>
                <button class="ios-notification-close" title="Close">✕</button>
            </div>
            <div class="ios-notification-message">${message}</div>
        `;

        // Add to container
        this.container.appendChild(notification);

        // Force reflow
        notification.offsetHeight;

        // Show with animation
        notification.classList.add('show');
        notification.classList.add('ios-notification-pulse');

        // Remove pulse animation after it completes
        setTimeout(() => {
            notification.classList.remove('ios-notification-pulse');
        }, 300);

        // Close button handler
        const closeButton = notification.querySelector('.ios-notification-close');
        closeButton.addEventListener('click', () => {
            this.hideNotification(notification);
        });

        // Auto-hide if enabled
        if (auto_hide) {
            setTimeout(() => {
                this.hideNotification(notification);
            }, duration);
        }

        // Play sound if available
        this.playSound(type);
    }

    hideNotification(notificationElement) {
        if (!notificationElement || !notificationElement.parentNode) return;

        notificationElement.classList.remove('show');
        notificationElement.classList.add('hide');

        // Remove after animation completes
        setTimeout(() => {
            if (notificationElement.parentNode) {
                notificationElement.parentNode.removeChild(notificationElement);
            }
            
            // Show next notification
            setTimeout(() => this.showNext(), 300);
        }, 500);
    }

    playSound(type) {
        // You can add sound effects here if desired
        // Example: different sounds for different notification types
        const soundMap = {
            'success': 'success.mp3',
            'error': 'error.mp3',
            'info': 'info.mp3',
            'warning': 'warning.mp3',
            'change': 'change.mp3'
        };

        // To implement sound, you would need audio files
        // For now, we'll just log the sound that would play
        if (soundMap[type]) {
            console.log(`Would play sound: ${soundMap[type]}`);
        }
    }

    checkSessionNotifications() {
        // Check for notifications stored in session
        console.log('Checking for session notifications...');
        const sessionNotification = window.sessionNotification || {};
        
        if (sessionNotification.type && sessionNotification.message) {
            console.log('Found session notification:', sessionNotification);
            // Show notification from session
            setTimeout(() => {
                console.log('Showing session notification after delay');
                this.show({
                    type: sessionNotification.type,
                    title: sessionNotification.title || 'Notification',
                    icon: sessionNotification.icon || 'ℹ️',
                    message: sessionNotification.message,
                    auto_hide: sessionNotification.auto_hide !== false,
                    duration: sessionNotification.duration || 4000
                });
                
                // Also send to Telegram if configured
                this.sendToTelegramIfAvailable(sessionNotification);
            }, 800); // Slightly shorter delay
            
            // Clear session notification
            delete window.sessionNotification;
        } else {
            console.log('No session notifications found');
        }
    }
    
    sendToTelegramIfAvailable(notification) {
        // This would send to your Telegram bot
        // For now, just log it
        console.log('Telegram notification would be sent:', {
            title: notification.title,
            message: notification.message,
            type: notification.type
        });
        
        // In a real implementation, you would make an API call here
        // Example:
        // fetch('/api/send-telegram/', {
        //     method: 'POST',
        //     headers: {'Content-Type': 'application/json'},
        //     body: JSON.stringify(notification)
        // });
    }

    // Public API methods
    success(title, message, duration = 4000) {
        this.show({
            type: 'success',
            title,
            icon: '✅',
            message,
            duration
        });
    }

    error(title, message, duration = 4000) {
        this.show({
            type: 'error',
            title,
            icon: '❌',
            message,
            duration
        });
    }

    info(title, message, duration = 4000) {
        this.show({
            type: 'info',
            title,
            icon: 'ℹ️',
            message,
            duration
        });
    }

    warning(title, message, duration = 4000) {
        this.show({
            type: 'warning',
            title,
            icon: '⚠️',
            message,
            duration
        });
    }

    change(title, message, duration = 4000) {
        this.show({
            type: 'change',
            title,
            icon: '🔄',
            message,
            duration
        });
    }
}

// Create global instance
window.IOSNotifications = new IOSNotificationSystem();

// Helper function to show notifications from Django template
function showIOSNotificationFromDjango(type, title, message, icon = null, duration = 4000) {
    const icons = {
        'success': '✅',
        'error': '❌',
        'info': 'ℹ️',
        'warning': '⚠️',
        'change': '🔄'
    };

    window.IOSNotifications.show({
        type: type,
        title: title,
        icon: icon || icons[type] || 'ℹ️',
        message: message,
        duration: duration
    });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IOSNotificationSystem;
}
/**
 * SIMPLE iOS Notification System
 * Guaranteed to work - minimal dependencies
 */

(function() {
    'use strict';
    
    console.log('Loading Simple Notification System...');
    
    // Create global namespace
    window.SimpleNotifications = {
        show: showNotification,
        success: showSuccess,
        error: showError,
        info: showInfo,
        warning: showWarning
    };
    
    // Queue for notifications
    let notificationQueue = [];
    let isShowing = false;
    
    // Create container once
    let notificationContainer = null;
    
    function init() {
        console.log('Initializing Simple Notification System...');
        
        // Remove any existing container
        const oldContainer = document.querySelector('.simple-notifications-container');
        if (oldContainer) {
            oldContainer.remove();
        }
        
        // Create new container
        notificationContainer = document.createElement('div');
        notificationContainer.className = 'simple-notifications-container';
        notificationContainer.style.cssText = `
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
        
        // Add styles
        addStyles();
        
        // Add to body
        document.body.appendChild(notificationContainer);
        console.log('Simple Notification container created');
        
        // Check for session notifications
        checkSessionNotifications();
    }
    
    function addStyles() {
        const styleId = 'simple-notifications-styles';
        if (document.getElementById(styleId)) return;
        
        const styles = `
            .simple-notification {
                position: relative;
                background: white;
                border-radius: 14px;
                padding: 16px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                opacity: 0;
                transform: translateX(100px);
                transition: all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
                pointer-events: auto;
                border: 1px solid rgba(0, 0, 0, 0.1);
                overflow: hidden;
                max-width: 350px;
                margin-bottom: 10px;
            }
            
            .simple-notification.show {
                opacity: 1;
                transform: translateX(0);
            }
            
            .simple-notification.hide {
                opacity: 0;
                transform: translateX(100px);
            }
            
            .simple-notification-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 8px;
            }
            
            .simple-notification-icon {
                font-size: 18px;
            }
            
            .simple-notification-title {
                font-size: 15px;
                font-weight: 600;
                color: #000;
                flex: 1;
            }
            
            .simple-notification-time {
                font-size: 12px;
                color: #666;
            }
            
            .simple-notification-message {
                font-size: 14px;
                line-height: 1.4;
                color: #333;
            }
            
            .simple-notification-close {
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
                color: #666;
                font-size: 14px;
                border: none;
                padding: 0;
            }
            
            .simple-notification:hover .simple-notification-close {
                opacity: 1;
            }
            
            /* Type colors */
            .simple-notification-success {
                border-left: 4px solid #4CAF50;
                background: #f1f8e9;
            }
            
            .simple-notification-error {
                border-left: 4px solid #f44336;
                background: #ffebee;
            }
            
            .simple-notification-info {
                border-left: 4px solid #2196F3;
                background: #e3f2fd;
            }
            
            .simple-notification-warning {
                border-left: 4px solid #ff9800;
                background: #fff3e0;
            }
            
            .simple-notification-change {
                border-left: 4px solid #9C27B0;
                background: #f3e5f5;
            }
            
            /* Dark mode */
            @media (prefers-color-scheme: dark) {
                .simple-notification {
                    background: #2d2d2d;
                    border-color: #444;
                }
                
                .simple-notification-title {
                    color: #fff;
                }
                
                .simple-notification-message {
                    color: #ccc;
                }
                
                .simple-notification-close {
                    background: rgba(255, 255, 255, 0.1);
                    color: #ccc;
                }
            }
        `;
        
        const styleElement = document.createElement('style');
        styleElement.id = styleId;
        styleElement.textContent = styles;
        document.head.appendChild(styleElement);
    }
    
    function showNotification(options) {
        const defaults = {
            type: 'info',
            title: 'Notification',
            icon: 'ℹ️',
            message: '',
            duration: 4000,
            autoHide: true
        };
        
        const config = { ...defaults, ...options };
        notificationQueue.push(config);
        
        if (!isShowing) {
            processQueue();
        }
    }
    
    function processQueue() {
        if (notificationQueue.length === 0) {
            isShowing = false;
            return;
        }
        
        isShowing = true;
        const config = notificationQueue.shift();
        createAndShowNotification(config);
    }
    
    function createAndShowNotification(config) {
        // Ensure container exists
        if (!notificationContainer || !document.body.contains(notificationContainer)) {
            init();
        }
        
        const notification = document.createElement('div');
        notification.className = `simple-notification simple-notification-${config.type}`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        notification.innerHTML = `
            <div class="simple-notification-header">
                <div class="simple-notification-icon">${config.icon}</div>
                <div class="simple-notification-title">${config.title}</div>
                <div class="simple-notification-time">${time}</div>
                <button class="simple-notification-close" title="Close">✕</button>
            </div>
            <div class="simple-notification-message">${config.message}</div>
        `;
        
        notificationContainer.appendChild(notification);
        
        // Force reflow
        notification.offsetHeight;
        
        // Show with animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Close button
        const closeButton = notification.querySelector('.simple-notification-close');
        closeButton.addEventListener('click', () => {
            hideNotification(notification);
        });
        
        // Auto-hide
        if (config.autoHide) {
            setTimeout(() => {
                hideNotification(notification);
            }, config.duration);
        }
    }
    
    function hideNotification(notification) {
        notification.classList.remove('show');
        notification.classList.add('hide');
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            processQueue();
        }, 500);
    }
    
    // Helper functions
    function showSuccess(title, message, duration = 4000) {
        showNotification({
            type: 'success',
            title: title,
            icon: '✅',
            message: message,
            duration: duration
        });
    }
    
    function showError(title, message, duration = 4000) {
        showNotification({
            type: 'error',
            title: title,
            icon: '❌',
            message: message,
            duration: duration
        });
    }
    
    function showInfo(title, message, duration = 4000) {
        showNotification({
            type: 'info',
            title: title,
            icon: 'ℹ️',
            message: message,
            duration: duration
        });
    }
    
    function showWarning(title, message, duration = 4000) {
        showNotification({
            type: 'warning',
            title: title,
            icon: '⚠️',
            message: message,
            duration: duration
        });
    }
    
    function checkSessionNotifications() {
        console.log('Checking for session notifications in Simple Notifications...');
        
        if (window.sessionNotification) {
            console.log('Found session notification:', window.sessionNotification);
            
            setTimeout(() => {
                showNotification({
                    type: window.sessionNotification.type,
                    title: window.sessionNotification.title || 'Notification',
                    icon: window.sessionNotification.icon || 'ℹ️',
                    message: window.sessionNotification.message,
                    duration: window.sessionNotification.duration || 4000,
                    autoHide: window.sessionNotification.auto_hide !== false
                });
                
                // Clear session notification
                delete window.sessionNotification;
            }, 1000);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    console.log('Simple Notification System loaded successfully!');
    
})();
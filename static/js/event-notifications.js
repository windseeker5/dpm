/**
 * Event Notifications Manager
 * Handles real-time notifications via Server-Sent Events (SSE)
 * Works with the existing notifications API blueprint
 */

class EventNotificationManager {
  constructor() {
    this.eventSource = null;
    this.container = null;
    this.notifications = new Map(); // Track active notifications
    this.maxNotifications = 5;
    this.autoDismissTimeout = 10000; // 10 seconds
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    
    this.init();
  }
  
  /**
   * Initialize the notification system
   */
  init() {
    this.createContainer();
    this.connectToStream();
    this.bindEvents();
    
    console.log('Event Notification Manager initialized');
  }
  
  /**
   * Create the notifications container if it doesn't exist
   */
  createContainer() {
    this.container = document.getElementById('notification-container');
    
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'notification-container';
      this.container.className = 'event-notifications-container';
      document.body.appendChild(this.container);
    }
  }
  
  /**
   * Connect to the SSE stream
   */
  connectToStream() {
    // Close existing connection
    if (this.eventSource) {
      this.eventSource.close();
    }
    
    try {
      this.eventSource = new EventSource('/api/event-stream');
      
      this.eventSource.onopen = (event) => {
        console.log('SSE connection established');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleNotification(data);
        } catch (error) {
          console.error('Error parsing SSE data:', error);
        }
      };
      
      this.eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        this.handleConnectionError();
      };
      
    } catch (error) {
      console.error('Error establishing SSE connection:', error);
      this.handleConnectionError();
    }
  }
  
  /**
   * Handle connection errors and implement reconnection logic
   */
  handleConnectionError() {
    if (this.eventSource) {
      this.eventSource.close();
    }
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connectToStream();
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.showReconnectionFailedMessage();
    }
  }
  
  /**
   * Show a message when reconnection fails
   */
  showReconnectionFailedMessage() {
    const notification = {
      type: 'error',
      id: 'connection_failed',
      data: {
        message: 'Connection to notification service lost. Please refresh the page.',
        persistent: true
      }
    };
    
    this.displayNotification(notification);
  }
  
  /**
   * Handle incoming notification data
   */
  handleNotification(data) {
    switch (data.type) {
      case 'payment':
        this.displayNotification(data);
        break;
      case 'signup':
        this.displayNotification(data);
        break;
      case 'heartbeat':
        // Heartbeat received, connection is healthy
        break;
      case 'error':
        console.error('Server error:', data.message);
        break;
      default:
        console.log('Unknown notification type:', data.type);
    }
  }
  
  /**
   * Display a notification
   */
  async displayNotification(notificationData) {
    // Enforce maximum notifications limit
    this.enforceNotificationLimit();
    
    try {
      // Fetch pre-rendered HTML from Flask
      const html = await this.fetchNotificationHTML(notificationData);
      
      // Create notification element
      const notificationElement = this.createNotificationElement(html, notificationData.id);
      
      // Add to container
      this.container.insertBefore(notificationElement, this.container.firstChild);
      
      // Track the notification
      this.notifications.set(notificationData.id, {
        element: notificationElement,
        data: notificationData,
        timestamp: Date.now()
      });
      
      // Show animation
      requestAnimationFrame(() => {
        notificationElement.classList.add('show');
      });
      
      // Auto-dismiss (unless persistent)
      if (!notificationData.data?.persistent) {
        setTimeout(() => {
          this.dismissNotification(notificationData.id);
        }, this.autoDismissTimeout);
      }
      
      // Play subtle notification sound
      this.playNotificationSound(notificationData.type === 'payment');
      
    } catch (error) {
      console.error('Error displaying notification:', error);
      this.displayFallbackNotification(notificationData);
    }
  }
  
  /**
   * Fetch pre-rendered HTML from Flask endpoint
   */
  async fetchNotificationHTML(notificationData) {
    const endpoint = notificationData.type === 'payment' 
      ? `/api/payment-notification-html/${notificationData.id}`
      : `/api/signup-notification-html/${notificationData.id}`;
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(notificationData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.text();
  }
  
  /**
   * Create notification element from HTML string
   */
  createNotificationElement(html, notificationId) {
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html.trim();
    const element = wrapper.firstElementChild;
    
    if (!element) {
      throw new Error('Invalid HTML received from server');
    }
    
    // Bind close button
    const closeBtn = element.querySelector('.btn-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.dismissNotification(notificationId);
      });
    }
    
    // Pause auto-dismiss on hover
    element.addEventListener('mouseenter', () => {
      const progressBar = element.querySelector('.notification-progress');
      if (progressBar) {
        progressBar.style.animationPlayState = 'paused';
      }
    });
    
    element.addEventListener('mouseleave', () => {
      const progressBar = element.querySelector('.notification-progress');
      if (progressBar) {
        progressBar.style.animationPlayState = 'running';
      }
    });
    
    return element;
  }
  
  /**
   * Display a fallback notification when HTML fetch fails
   */
  displayFallbackNotification(notificationData) {
    const fallbackHTML = this.generateFallbackHTML(notificationData);
    const notificationElement = this.createNotificationElement(fallbackHTML, notificationData.id);
    
    this.container.insertBefore(notificationElement, this.container.firstChild);
    
    this.notifications.set(notificationData.id, {
      element: notificationElement,
      data: notificationData,
      timestamp: Date.now()
    });
    
    requestAnimationFrame(() => {
      notificationElement.classList.add('show');
    });
    
    setTimeout(() => {
      this.dismissNotification(notificationData.id);
    }, this.autoDismissTimeout);
  }
  
  /**
   * Generate fallback HTML for notifications
   */
  generateFallbackHTML(notificationData) {
    const type = notificationData.type;
    const data = notificationData.data;
    const isPayment = type === 'payment';
    
    return `
      <div class="alert alert-dismissible event-notification notification-${type}" role="alert" data-notification-id="${notificationData.id}">
        <button type="button" class="btn-close">
          <i class="ti ti-x"></i>
        </button>
        <div class="notification-content">
          <div class="notification-header">
            <div class="notification-avatar">
              <span class="avatar avatar-md" style="background-image: url('${data.avatar || ''}')">
                <i class="ti ti-user"></i>
              </span>
            </div>
            <div class="notification-title-area">
              <div class="notification-title">
                <i class="ti ${isPayment ? 'ti-credit-card' : 'ti-user-plus'} notification-icon"></i>
                <span class="notification-title-text">${isPayment ? 'Payment Received' : 'New Registration'}</span>
              </div>
              <div class="notification-subtitle text-muted">
                ${data.user_name || 'Unknown User'}
                <span class="notification-email">${data.email || ''}</span>
              </div>
            </div>
          </div>
          <div class="notification-body">
            <div class="notification-activity">
              <strong>${data.activity || 'Unknown Activity'}</strong>
            </div>
            ${isPayment ? 
              `<div class="notification-amount">
                <span class="text-green fw-bold">$${(data.amount || 0).toFixed(2)}</span>
              </div>` :
              `<div class="notification-signup-details">
                ${data.passport_type ? `<span class="badge badge-outline text-blue">${data.passport_type}</span>` : ''}
                ${data.passport_type_price ? `<span class="text-muted ms-2">$${data.passport_type_price.toFixed(2)}</span>` : ''}
              </div>`
            }
          </div>
          <div class="notification-footer">
            <div class="notification-status">
              <i class="ti ${isPayment ? 'ti-check text-green' : 'ti-clock text-blue'}"></i>
              <span class="${isPayment ? 'text-green' : 'text-blue'}">${isPayment ? 'Payment Confirmed' : 'Registration Pending'}</span>
            </div>
          </div>
        </div>
        <div class="notification-progress"></div>
      </div>
    `;
  }
  
  /**
   * Dismiss a specific notification
   */
  dismissNotification(notificationId) {
    const notification = this.notifications.get(notificationId);
    
    if (!notification) {
      return;
    }
    
    // Add hide animation
    notification.element.classList.add('hide');
    notification.element.classList.remove('show');
    
    // Remove after animation
    setTimeout(() => {
      if (notification.element.parentNode) {
        notification.element.remove();
      }
      this.notifications.delete(notificationId);
    }, 400);
  }
  
  /**
   * Enforce maximum number of notifications
   */
  enforceNotificationLimit() {
    if (this.notifications.size >= this.maxNotifications) {
      // Remove oldest notifications
      const sortedNotifications = Array.from(this.notifications.entries())
        .sort((a, b) => a[1].timestamp - b[1].timestamp);
      
      const toRemove = sortedNotifications.slice(0, this.notifications.size - this.maxNotifications + 1);
      
      toRemove.forEach(([id, notification]) => {
        this.dismissNotification(id);
      });
    }
  }
  
  /**
   * Play subtle notification sound
   */
  playNotificationSound(isPayment = false) {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      // Different frequencies for different notification types
      oscillator.frequency.setValueAtTime(isPayment ? 880 : 660, audioContext.currentTime);
      oscillator.type = 'sine';
      
      // Very subtle volume
      gainNode.gain.setValueAtTime(0, audioContext.currentTime);
      gainNode.gain.linearRampToValueAtTime(0.015, audioContext.currentTime + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.15);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.15);
      
    } catch (error) {
      // Silent fail if audio is not supported
    }
  }
  
  /**
   * Bind global events
   */
  bindEvents() {
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Page is hidden, reduce activity
      } else {
        // Page is visible, ensure connection is active
        if (!this.eventSource || this.eventSource.readyState === EventSource.CLOSED) {
          console.log('Reconnecting due to page visibility change');
          this.connectToStream();
        }
      }
    });
    
    // Handle window beforeunload
    window.addEventListener('beforeunload', () => {
      if (this.eventSource) {
        this.eventSource.close();
      }
    });
  }
  
  /**
   * Manually dismiss all notifications
   */
  dismissAll() {
    const notificationIds = Array.from(this.notifications.keys());
    notificationIds.forEach(id => this.dismissNotification(id));
  }
  
  /**
   * Get count of active notifications
   */
  getActiveCount() {
    return this.notifications.size;
  }
  
  /**
   * Destroy the manager (cleanup)
   */
  destroy() {
    if (this.eventSource) {
      this.eventSource.close();
    }
    
    this.dismissAll();
    
    if (this.container && this.container.parentNode) {
      this.container.remove();
    }
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize for admin users
  if (document.body.dataset.adminUser) {
    window.eventNotificationManager = new EventNotificationManager();
  }
});

// Export for manual use
window.EventNotificationManager = EventNotificationManager;
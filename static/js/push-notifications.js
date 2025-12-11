// Minipass Push Notifications Manager
// Handles browser push notification subscription and management

const MinipassPush = {

  // Check if push notifications are supported
  isSupported() {
    return 'serviceWorker' in navigator &&
           'PushManager' in window &&
           'Notification' in window;
  },

  // Get current permission state
  getPermissionState() {
    return Notification.permission;
  },

  // Convert URL-safe base64 to Uint8Array (required for applicationServerKey)
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    const rawData = window.atob(base64);
    return Uint8Array.from([...rawData].map(c => c.charCodeAt(0)));
  },

  // Subscribe to push notifications
  async subscribe() {
    if (!this.isSupported()) {
      throw new Error('Push notifications not supported in this browser');
    }

    // Request permission
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      throw new Error('Notification permission denied');
    }

    // Get VAPID public key from server
    const keyResponse = await fetch('/api/push/vapid-public-key');
    if (!keyResponse.ok) {
      throw new Error('Failed to get VAPID public key');
    }
    const { publicKey } = await keyResponse.json();

    // Get service worker registration
    const registration = await navigator.serviceWorker.ready;

    // Subscribe to push manager
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: this.urlBase64ToUint8Array(publicKey)
    });

    // Send subscription to server
    const response = await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subscription: subscription.toJSON() })
    });

    if (!response.ok) {
      throw new Error('Failed to save subscription on server');
    }

    console.log('[Push] Successfully subscribed to push notifications');
    return subscription;
  },

  // Unsubscribe from push notifications
  async unsubscribe() {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      await subscription.unsubscribe();

      // Notify server to remove subscription
      await fetch('/api/push/unsubscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: subscription.endpoint })
      });

      console.log('[Push] Successfully unsubscribed from push notifications');
    }

    return true;
  },

  // Check if currently subscribed
  async isSubscribed() {
    if (!this.isSupported()) return false;

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      return !!subscription;
    } catch (e) {
      return false;
    }
  },

  // Initialize a toggle switch element
  async initToggle(toggleElement, statusElement) {
    if (!toggleElement) return;

    // Check browser support
    if (!this.isSupported()) {
      toggleElement.disabled = true;
      if (statusElement) {
        statusElement.textContent = 'Push notifications are not supported in this browser.';
      }
      return;
    }

    // Set initial state based on current subscription
    const isSubscribed = await this.isSubscribed();
    toggleElement.checked = isSubscribed;

    if (statusElement) {
      this.updateStatusText(statusElement, isSubscribed);
    }

    // Handle toggle changes
    toggleElement.addEventListener('change', async (e) => {
      const wasChecked = !e.target.checked; // Previous state
      toggleElement.disabled = true; // Prevent rapid clicks

      try {
        if (e.target.checked) {
          await this.subscribe();
          if (statusElement) {
            this.updateStatusText(statusElement, true);
          }
        } else {
          await this.unsubscribe();
          if (statusElement) {
            this.updateStatusText(statusElement, false);
          }
        }
      } catch (err) {
        console.error('[Push] Toggle error:', err);
        // Revert toggle state on error
        e.target.checked = wasChecked;
        if (statusElement) {
          statusElement.textContent = err.message;
          statusElement.style.color = '#dc3545';
        }
      } finally {
        toggleElement.disabled = false;
      }
    });
  },

  // Update status text based on subscription state
  updateStatusText(statusElement, isSubscribed) {
    statusElement.style.color = '';
    if (isSubscribed) {
      statusElement.textContent = 'You will receive notifications for new signups and payments.';
    } else {
      statusElement.textContent = 'Enable to receive instant alerts when someone signs up or payments are processed.';
    }
  }
};

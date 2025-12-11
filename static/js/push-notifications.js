// Minipass Push Notifications Manager
const MinipassPush = {
  isSupported() {
    return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  },

  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    return Uint8Array.from([...rawData].map(c => c.charCodeAt(0)));
  },

  async subscribe() {
    if (!this.isSupported()) throw new Error('Push not supported');

    const permission = await Notification.requestPermission();
    if (permission !== 'granted') throw new Error('Permission denied');

    const keyResponse = await fetch('/api/push/vapid-public-key');
    if (!keyResponse.ok) throw new Error('Failed to get VAPID key');
    const { publicKey } = await keyResponse.json();

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: this.urlBase64ToUint8Array(publicKey)
    });

    const response = await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subscription: subscription.toJSON() })
    });
    if (!response.ok) throw new Error('Failed to save subscription');

    return subscription;
  },

  async unsubscribe() {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    if (subscription) {
      await subscription.unsubscribe();
      await fetch('/api/push/unsubscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: subscription.endpoint })
      });
    }
    return true;
  },

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

  async initToggle(toggleElement, statusElement) {
    if (!toggleElement || !this.isSupported()) {
      if (statusElement) statusElement.textContent = 'Push notifications not supported';
      return;
    }

    const isSubscribed = await this.isSubscribed();
    toggleElement.checked = isSubscribed;
    if (statusElement) {
      statusElement.textContent = isSubscribed
        ? 'You will receive notifications for signups and payments.'
        : 'Enable to receive alerts for signups and payments.';
    }

    toggleElement.addEventListener('change', async (e) => {
      toggleElement.disabled = true;
      try {
        if (e.target.checked) {
          await this.subscribe();
          if (statusElement) statusElement.textContent = 'You will receive notifications for signups and payments.';
        } else {
          await this.unsubscribe();
          if (statusElement) statusElement.textContent = 'Enable to receive alerts for signups and payments.';
        }
      } catch (err) {
        e.target.checked = !e.target.checked;
        if (statusElement) {
          statusElement.textContent = err.message;
          statusElement.style.color = '#dc3545';
        }
      } finally {
        toggleElement.disabled = false;
      }
    });
  }
};

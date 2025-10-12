class PushNotificationManager {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.subscription = null;
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.log('Push notifications are not supported');
            return;
        }

        try {
            // Регистрируем Service Worker
            const registration = await navigator.serviceWorker.register('/static/events/js/sw.js');
            console.log('ServiceWorker registered');

            // Проверяем подписку
            this.subscription = await registration.pushManager.getSubscription();
            
            if (this.subscription) {
                console.log('User is subscribed to push notifications');
                this.sendSubscriptionToServer(this.subscription, 'subscribe');
            }

            // Слушаем сообщения от Service Worker
            navigator.serviceWorker.addEventListener('message', this.handleServiceWorkerMessage.bind(this));

        } catch (error) {
            console.error('ServiceWorker registration failed:', error);
        }
    }

    async subscribeUser() {
        if (!this.isSupported) {
            throw new Error('Push notifications are not supported');
        }

        try {
            const registration = await navigator.serviceWorker.ready;
            
            // Запрашиваем разрешение
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                throw new Error('Permission not granted for notifications');
            }

            // Подписываем пользователя
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array('{{ VAPID_PUBLIC_KEY }}')
            });

            this.subscription = subscription;
            await this.sendSubscriptionToServer(subscription, 'subscribe');
            
            return subscription;

        } catch (error) {
            console.error('Failed to subscribe user:', error);
            throw error;
        }
    }

    async unsubscribeUser() {
        if (!this.subscription) {
            return;
        }

        try {
            await this.subscription.unsubscribe();
            await this.sendSubscriptionToServer(this.subscription, 'unsubscribe');
            this.subscription = null;
            
        } catch (error) {
            console.error('Failed to unsubscribe user:', error);
            throw error;
        }
    }

    async sendSubscriptionToServer(subscription, action) {
        const response = await fetch('/api/notifications/subscription/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                subscription: subscription,
                action: action
            })
        });

        if (!response.ok) {
            throw new Error('Failed to send subscription to server');
        }

        return await response.json();
    }

    handleServiceWorkerMessage(event) {
        const { type, data } = event.data;
        
        switch (type) {
            case 'NOTIFICATION_CLICK':
                this.handleNotificationClick(data);
                break;
            case 'BACKGROUND_SYNC':
                this.handleBackgroundSync(data);
                break;
        }
    }

    handleNotificationClick(data) {
        // Обработка клика по уведомлению
        if (data.url) {
            window.location.href = data.url;
        }
    }

    handleBackgroundSync(data) {
        console.log('Background sync completed:', data);
    }

    // Вспомогательные методы
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Дополнительные методы для управления уведомлениями
    async showLocalNotification(title, options) {
        if (!this.isSupported) return;

        const registration = await navigator.serviceWorker.ready;
        await registration.showNotification(title, options);
    }

    // Метод для проверки статуса подписки
    getSubscriptionStatus() {
        return {
            isSupported: this.isSupported,
            isSubscribed: !!this.subscription
        };
    }

    // Метод для обновления подписки
    async updateSubscription() {
        if (this.subscription) {
            await this.unsubscribeUser();
        }
        return await this.subscribeUser();
    }
}
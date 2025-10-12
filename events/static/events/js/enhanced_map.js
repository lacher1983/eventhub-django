class EnhancedEventMap {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.map = null;
        this.clusterer = null;
        this.markers = [];
        this.filters = new EventFilters(this);
        this.heatmap = null;
        
        this.options = {
            center: [55.76, 37.64],
            zoom: 10,
            heatmapEnabled: true,
            ...options
        };
        
        this.initMap();
    }

    initMap() {
        // Инициализация Яндекс.Карт с улучшенными настройками
        ymaps.ready(() => {
            this.map = new ymaps.Map(this.container, {
                center: this.options.center,
                zoom: this.options.zoom,
                controls: ['zoomControl', 'fullscreenControl', 'typeSelector']
            });

            // Включаем кластеризацию
            this.clusterer = new ymaps.Clusterer({
                clusterDisableClickZoom: true,
                clusterOpenBalloonOnClick: true,
                clusterBalloonContentLayout: 'cluster#balloonCarousel',
                clusterBalloonItemContentLayout: this.createClusterItemLayout(),
                clusterBalloonPanelMaxMapArea: 0,
                clusterBalloonContentLayoutWidth: 300,
                clusterBalloonContentLayoutHeight: 200,
                clusterBalloonPagerSize: 5
            });

            this.map.geoObjects.add(this.clusterer);

            // Инициализация тепловой карты если включено
            if (this.options.heatmapEnabled) {
                this.initHeatmap();
            }

            // Загрузка мероприятий
            this.loadEvents();

            // Добавляем кастомные контролы
            this.addCustomControls();
        });
    }

    initHeatmap() {
        // Создание тепловой карты плотности мероприятий
        this.heatmap = new ymaps.Heatmap({
            radius: 30,
            dissipating: false,
            opacity: 0.8,
            intensityOfMidpoint: 0.2,
            gradient: {
                0.1: 'rgba(128, 255, 0, 0.7)',
                0.2: 'rgba(255, 255, 0, 0.8)',
                0.7: 'rgba(234, 72, 58, 0.9)',
                1.0: 'rgba(162, 36, 25, 1)'
            }
        });

        this.map.geoObjects.add(this.heatmap);
    }

    addCustomControls() {
        // Кнопка переключения тепловой карты
        const heatmapToggle = new ymaps.control.Button({
            data: { content: '🔥 Тепловая карта' },
            options: { selectOnClick: true }
        });

        heatmapToggle.events.add('select', () => {
            if (this.heatmap) {
                this.map.geoObjects.add(this.heatmap);
            }
        });

        heatmapToggle.events.add('deselect', () => {
            if (this.heatmap) {
                this.map.geoObjects.remove(this.heatmap);
            }
        });

        this.map.controls.add(heatmapToggle, { float: 'right' });

        // Кнопка геолокации
        const geolocationButton = new ymaps.control.Button({
            data: { content: '📍 Мое местоположение' }
        });

        geolocationButton.events.add('press', () => {
            this.locateUser();
        });

        this.map.controls.add(geolocationButton, { float: 'right' });
    }

    locateUser() {
        // Определение местоположения пользователя
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const userLocation = [
                        position.coords.latitude,
                        position.coords.longitude
                    ];

                    // Создаем маркер местоположения пользователя
                    const userMarker = new ymaps.Placemark(userLocation, {
                        balloonContent: 'Ваше местоположение'
                    }, {
                        preset: 'islands#blueCircleIcon',
                        draggable: false
                    });

                    this.map.geoObjects.add(userMarker);
                    this.map.setCenter(userLocation, 13);

                    // Показываем ближайшие мероприятия
                    this.showNearestEvents(userLocation);
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    alert('Не удалось определить ваше местоположение');
                }
            );
        }
    }

    async showNearestEvents(userLocation) {
        // Показываем мероприятия ближайшие к пользователю
        try {
            const response = await fetch(`/api/events/nearby/?lat=${userLocation[0]}&lon=${userLocation[1]}&radius=10`);
            const events = await response.json();

            events.forEach(event => {
                this.addEventMarker(event, true); // true - highlight nearby events
            });
        } catch (error) {
            console.error('Error loading nearby events:', error);
        }
    }

    createClusterItemLayout() {
        // Кастомный layout для кластеров
        return ymaps.templateLayoutFactory.createClass(
            '<div class="cluster-balloon">' +
                '<h3>Мероприятия в этой области</h3>' +
                '<div class="cluster-events">' +
                    '{% for event in properties.events %}' +
                    '<div class="cluster-event-item">' +
                        '<strong>{{ event.title }}</strong><br>' +
                        '<small>{{ event.date }}</small>' +
                    '</div>' +
                    '{% endfor %}' +
                '</div>' +
            '</div>'
        );
    }

    createEventBalloonContent(event) {
        // Создание красивого балуна для мероприятия
        const badges = event.badges && event.badges.length > 0 ? 
            event.badges.map(badge => `<span class="badge badge-${badge}">${this.getBadgeText(badge)}</span>`).join('') : 
            '';
        
        const date = new Date(event.date).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            hour: '2-digit',
            minute: '2-digit'
        });

        return `
            <div class="event-balloon">
                <div class="event-balloon-header">
                    <h4>${event.title}</h4>
                    <div class="event-badges">${badges}</div>
                </div>
                <div class="event-balloon-content">
                    <p><strong>📅 Дата:</strong> ${date}</p>
                    <p><strong>📍 Место:</strong> ${event.location}</p>
                    <p><strong>💰 Цена:</strong> ${event.price > 0 ? event.price + '₽' : 'Бесплатно'}</p>
                    <p><strong>👥 Организатор:</strong> ${event.organizer_name}</p>
                    ${event.available_spots ? `<p><strong>🎫 Осталось мест:</strong> ${event.available_spots}</p>` : ''}
                </div>
                <div class="event-balloon-actions">
                    <a href="/event/${event.id}/" class="btn btn-primary btn-sm">Подробнее</a>
                    <button class="btn btn-outline-secondary btn-sm" onclick="addToFavorites(${event.id})">
                        ❤️ В избранное
                    </button>
                </div>
            </div>
        `;
    }

    getBadgeText(badgeType) {
        const badgeTexts = {
            'trending': '🔥 Популярное',
            'new': '🆕 Новое',
            'featured': '⭐ Рекомендуем',
            'early_bird': '🐦 Ранняя пташка',
            'last_chance': '⏰ Последний шанс',
            'sold_out': '🔴 Продано',
            'exclusive': '👑 Эксклюзив',
            'discount': '💸 Скидка',
            'online': '💻 Онлайн',
            'free': '🎫 Бесплатно'
        };
        return badgeTexts[badgeType] || badgeType;
    }

    async loadEvents() {
        try {
            const response = await fetch('/api/events/?format=json&map=true');
            const events = await response.json();
            
            this.renderEvents(events);
            this.updateHeatmap(events);
            
        } catch (error) {
            console.error('Error loading events:', error);
        }
    }

    renderEvents(events) {
        // Очищаем предыдущие маркеры
        this.clusterer.removeAll();
        this.markers = [];

        events.forEach(event => {
            if (event.latitude && event.longitude) {
                this.addEventMarker(event);
            }
        });

        // Обновляем статистику
        this.updateEventsStats(events);
    }

    addEventMarker(event, isHighlighted = false) {
        const coordinates = [event.latitude, event.longitude];
        
        const marker = new ymaps.Placemark(coordinates, {
            balloonContent: this.createEventBalloonContent(event),
            hintContent: event.title,
            eventData: event // Сохраняем данные события для фильтрации
        }, {
            preset: this.getEventPreset(event),
            balloonCloseButton: true,
            hideIconOnBalloonOpen: false,
            balloonOffset: [0, -40]
        });

        // Добавляем обработчики событий
        marker.events.add('click', (e) => {
            this.onEventClick(event, marker);
        });

        marker.events.add('balloonopen', (e) => {
            this.trackEventView(event.id);
        });

        this.clusterer.add(marker);
        this.markers.push(marker);

        if (isHighlighted) {
            this.highlightMarker(marker);
        }
    }

    getEventPreset(event) {
        // Разные иконки для разных типов мероприятий
        const presetMap = {
            'concert': 'islands#redMusicIcon',
            'conference': 'islands#blueConferenceIcon',
            'workshop': 'islands#greenWorkshopIcon',
            'sport_event': 'islands#orangeSportIcon',
            'exhibition': 'islands#violetExhibitionIcon',
            'party': 'islands#pinkPartyIcon',
            'default': 'islands#blueEventIcon'
        };

        return presetMap[event.event_type] || presetMap.default;
    }

    updateHeatmap(events) {
        if (!this.heatmap) return;

        const points = events
            .filter(event => event.latitude && event.longitude)
            .map(event => {
                return {
                    type: 'Point',
                    coordinates: [event.latitude, event.longitude],
                    properties: {
                        weight: this.calculateEventWeight(event)
                    }
                };
            });

        this.heatmap.setData(points);
    }

    calculateEventWeight(event) {
        // Вес для тепловой карты на основе популярности
        let weight = 1;
        
        if (event.registrations_count > 50) weight += 2;
        if (event.registrations_count > 100) weight += 3;
        if (event.average_rating > 4.5) weight += 1;
        if (event.badges && event.badges.includes('trending')) weight += 2;
        
        return Math.min(weight, 5);
    }

    updateEventsStats(events) {
        const stats = {
            total: events.length,
            withCoordinates: events.filter(e => e.latitude && e.longitude).length,
            categories: this.countByCategory(events),
            today: events.filter(e => this.isToday(e.date)).length
        };

        this.updateStatsDisplay(stats);
    }

    countByCategory(events) {
        return events.reduce((acc, event) => {
            const category = event.category_name || 'Другое';
            acc[category] = (acc[category] || 0) + 1;
            return acc;
        }, {});
    }

    isToday(dateString) {
        const eventDate = new Date(dateString);
        const today = new Date();
        return eventDate.toDateString() === today.toDateString();
    }

    updateStatsDisplay(stats) {
        const statsElement = document.getElementById('map-stats');
        if (statsElement) {
            statsElement.innerHTML = `
                <div class="map-stats">
                    <span class="stat-item">🗺️ ${stats.withCoordinates} на карте</span>
                    <span class="stat-item">📅 ${stats.today} сегодня</span>
                    <span class="stat-item">🎯 ${stats.total} всего</span>
                </div>
            `;
        }
    }

    onEventClick(event, marker) {
        // Трекинг кликов для аналитики
        this.trackEventClick(event.id);
        
        // Показываем дополнительную информацию
        this.showEventDetails(event);
    }

    trackEventView(eventId) {
        // Отправка данных о просмотре
        fetch(`/api/events/${eventId}/track_view/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json'
            }
        });
    }

    trackEventClick(eventId) {
        // Отправка данных о клике
        fetch(`/api/events/${eventId}/track_click/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json'
            }
        });
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    showEventDetails(event) {
        // Показываем детали события в сайдбаре
        const sidebar = document.getElementById('event-sidebar');
        if (sidebar) {
            sidebar.innerHTML = this.createEventSidebarContent(event);
            sidebar.classList.add('active');
        }
    }

    createEventSidebarContent(event) {
        return `
            <div class="event-sidebar-content">
                <button class="close-sidebar" onclick="this.parentElement.parentElement.classList.remove('active')">
                    &times;
                </button>
                <h3>${event.title}</h3>
                <div class="event-meta">
                    <span class="event-category">${event.category_name}</span>
                    <span class="event-type">${event.event_type_name}</span>
                </div>
                <p class="event-description">${event.short_description}</p>
                <div class="event-actions">
                    <a href="/event/${event.id}/" class="btn btn-primary">Подробнее</a>
                    <button class="btn btn-success" onclick="registerForEvent(${event.id})">
                        Зарегистрироваться
                    </button>
                </div>
            </div>
        `;
    }

    highlightMarker(marker) {
        // Подсветка маркера
        marker.options.set('preset', 'islands#redIcon');
        setTimeout(() => {
            marker.options.set('preset', this.getEventPreset(marker.properties.get('eventData')));
        }, 3000);
    }
}

// Класс для фильтров карты
class EventFilters {
    constructor(mapInstance) {
        this.map = mapInstance;
        this.activeFilters = new Set();
        this.initFilters();
    }

    initFilters() {
        this.setupCategoryFilter();
        this.setupPriceFilter();
        this.setupDateFilter();
        this.setupSearchFilter();
    }

    setupCategoryFilter() {
        const categorySelect = document.getElementById('category-filter');
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => {
                this.filterByCategory(e.target.value);
            });
        }
    }

    setupPriceFilter() {
        const priceSelect = document.getElementById('price-filter');
        if (priceSelect) {
            priceSelect.addEventListener('change', (e) => {
                this.filterByPrice(e.target.value);
            });
        }
    }

    setupDateFilter() {
        const dateSelect = document.getElementById('date-filter');
        if (dateSelect) {
            dateSelect.addEventListener('change', (e) => {
                this.filterByDate(e.target.value);
            });
        }
    }

    setupSearchFilter() {
        const searchInput = document.getElementById('map-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterBySearch(e.target.value);
            });
        }
    }

    filterByCategory(category) {
        if (category === 'all') {
            this.activeFilters.delete('category');
        } else {
            this.activeFilters.add('category');
        }
        this.applyFilters();
    }

    filterByPrice(priceType) {
        if (priceType === 'all') {
            this.activeFilters.delete('price');
        } else {
            this.activeFilters.add('price');
        }
        this.applyFilters();
    }

    filterByDate(dateRange) {
        if (dateRange === 'all') {
            this.activeFilters.delete('date');
        } else {
            this.activeFilters.add('date');
        }
        this.applyFilters();
    }

    filterBySearch(searchTerm) {
        if (!searchTerm) {
            this.activeFilters.delete('search');
        } else {
            this.activeFilters.add('search');
        }
        this.applyFilters();
    }

    applyFilters() {
        this.map.markers.forEach(marker => {
            const event = marker.properties.get('eventData');
            const isVisible = this.isEventVisible(event);
            marker.options.set('visible', isVisible);
        });
        
        this.map.clusterer.repaint();
    }

    isEventVisible(event) {
        // Применяем все активные фильтры
        for (let filter of this.activeFilters) {
            if (!this[`check${filter.charAt(0).toUpperCase() + filter.slice(1)}`](event)) {
                return false;
            }
        }
        return true;
    }

    checkCategory(event) {
        const selectedCategory = document.getElementById('category-filter').value;
        return selectedCategory === 'all' || event.category === selectedCategory;
    }

    checkPrice(event) {
        const selectedPrice = document.getElementById('price-filter').value;
        switch (selectedPrice) {
            case 'free': return event.price === 0;
            case 'paid': return event.price > 0;
            case 'all': return true;
            default: return true;
        }
    }

    checkDate(event) {
        const selectedDate = document.getElementById('date-filter').value;
        const eventDate = new Date(event.date);
        const today = new Date();
        
        switch (selectedDate) {
            case 'today':
                return eventDate.toDateString() === today.toDateString();
            case 'week':
                const weekLater = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
                return eventDate >= today && eventDate <= weekLater;
            case 'month':
                const monthLater = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
                return eventDate >= today && eventDate <= monthLater;
            case 'all':
            default:
                return true;
        }
    }

    checkSearch(event) {
        const searchTerm = document.getElementById('map-search').value.toLowerCase();
        if (!searchTerm) return true;
        
        return event.title.toLowerCase().includes(searchTerm) ||
               event.description.toLowerCase().includes(searchTerm) ||
               event.location.toLowerCase().includes(searchTerm);
    }
}

// Глобальные функции для использования в шаблонах
function initEventMap(containerId = 'map', options = {}) {
    window.eventMap = new EnhancedEventMap(containerId, options);
}

function addToFavorites(eventId) {
    fetch(`/event/${eventId}/favorite/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
      .then(data => {
          if (data.status === 'added') {
              showNotification('Мероприятие добавлено в избранное', 'success');
          } else {
              showNotification('Мероприятие удалено из избранного', 'info');
          }
      });
}

function registerForEvent(eventId) {
    window.location.href = `/event/${eventId}/register/`;
}

function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function showNotification(message, type = 'info') {
    // Простая реализация уведомлений
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 300px;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
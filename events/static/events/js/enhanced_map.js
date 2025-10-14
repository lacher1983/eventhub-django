class EnhancedEventMap {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }
        
        // Проверяем, не инициализирована ли уже карта в этом контейнере
        if (window.activeMaps && window.activeMaps[containerId]) {
            console.warn(`Map already initialized in container #${containerId}`);
            return window.activeMaps[containerId];
        }
        
        // Инициализируем глобальный реестр карт
        if (!window.activeMaps) {
            window.activeMaps = {};
        }
        
        this.map = null;
        this.clusterer = null;
        this.markers = [];
        this.filters = null;
        this.userLocation = null;
        this.userPlacemark = null;
        this.heatmap = null;
        this.isInitialized = false;
        
        this.options = {
            center: [55.76, 37.64],
            zoom: 10,
            heatmapEnabled: true,
            clusteringEnabled: true,
            userLocation: null,
            filters: {
                radius: null,
                rating: null,
                participants: null,
                category: 'all',
                price: 'all',
                date: 'all',
                search: ''
            },
            eventsData: [], // Данные мероприятий
            ...options
        };
        
        // Регистрируем карту в глобальном реестре
        window.activeMaps[containerId] = this;
        
        this.init();
    }

    async init() {
        await this.loadYmaps();
        this.initMap();
        this.setupEventListeners();
        this.setupAdvancedFilters();
        this.loadEvents();
    }

    loadYmaps() {
        return new Promise((resolve) => {
            if (window.ymaps) {
                ymaps.ready(resolve);
                return;
            }
            
            const script = document.createElement('script');
            script.src = `https://api-maps.yandex.ru/2.1/?apikey=${this.options.apiKey || 'your-api-key'}&lang=ru_RU`;
            script.onload = () => ymaps.ready(resolve);
            document.head.appendChild(script);
        });
    }

    initMap() {
        if (this.isInitialized) {
            console.warn('Map is already initialized');
            return;
        }

        if (typeof ymaps === 'undefined') {
            console.error('Yandex Maps API not loaded');
            this.showFallbackMap();
            return;
        }

        ymaps.ready(() => {
            // Дополнительная проверка перед инициализацией
            if (this.container.querySelector('.ymaps-2-1-79-inner-panes')) {
                console.warn('Map container already contains map elements');
                return;
            }

            try {
                // Очищаем контейнер
                this.cleanupContainer();
                
                this.map = new ymaps.Map(this.container, {
                    center: this.options.center,
                    zoom: this.options.zoom,
                    controls: ['zoomControl', 'fullscreenControl', 'typeSelector']
                });

                this.isInitialized = true;

                this.initClusterer();
                this.filters = new EventFilters(this);
                
                if (this.options.heatmapEnabled) {
                    this.initHeatmap();
                }

                // Загружаем мероприятия (из переданных данных или через API)
                if (this.options.eventsData && this.options.eventsData.length > 0) {
                    console.log('Using preloaded events data:', this.options.eventsData.length);
                    this.renderEvents(this.options.eventsData);
                    this.updateHeatmap(this.options.eventsData);
                } else {
                    this.loadEvents();
                }

                this.addCustomControls();

                console.log('Map initialized successfully');
                document.getElementById('map-loading')?.remove();

            } catch (error) {
                console.error('Error initializing map:', error);
                this.showFallbackMap();
            }
        });
    }

    // НОВАЯ ФУНКЦИОНАЛЬНОСТЬ: Расширенные фильтры
    setupAdvancedFilters() {
        this.setupRadiusFilter();
        this.setupRatingFilter();
        this.setupParticipantsFilter();
        this.setupUserLocation();
    }

    setupRadiusFilter() {
        const radiusSlider = document.getElementById('radius-filter');
        const radiusValue = document.getElementById('radius-value');
        
        if (radiusSlider && radiusValue) {
            radiusSlider.addEventListener('input', (e) => {
                const radius = parseInt(e.target.value);
                radiusValue.textContent = radius === 0 ? 'Любой' : `${radius} км`;
                this.options.filters.radius = radius === 0 ? null : radius;
                this.applyFilters();
            });
        }
    }

    setupRatingFilter() {
        const ratingSelect = document.getElementById('rating-filter');
        if (ratingSelect) {
            ratingSelect.addEventListener('change', (e) => {
                this.options.filters.rating = e.target.value === 'all' ? null : parseFloat(e.target.value);
                this.applyFilters();
            });
        }
    }

    setupParticipantsFilter() {
        const participantsSelect = document.getElementById('participants-filter');
        if (participantsSelect) {
            participantsSelect.addEventListener('change', (e) => {
                this.options.filters.participants = e.target.value === 'all' ? null : parseInt(e.target.value);
                this.applyFilters();
            });
        }
    }

    setupUserLocation() {
        const locateBtn = document.getElementById('locate-user-btn');
        if (locateBtn) {
            locateBtn.addEventListener('click', () => {
                this.locateUser();
            });
        }
    }

    // ОБНОВЛЕННАЯ ФУНКЦИОНАЛЬНОСТЬ: Применение фильтров
    applyFilters() {
        if (!this.markers || this.markers.length === 0) return;
        
        let visibleCount = 0;
        
        this.markers.forEach(marker => {
            const event = marker.properties.get('eventData');
            const isVisible = this.isEventVisible(event);
            
            marker.options.set('visible', isVisible);
            
            if (isVisible) {
                visibleCount++;
            }
        });
        
        this.updateVisibleStats(visibleCount);
        
        if (this.clusterer) {
            this.clusterer.repaint();
        }
    }

    isEventVisible(event) {
        // Существующие фильтры
        if (!this.checkCategory(event)) return false;
        if (!this.checkPrice(event)) return false;
        if (!this.checkDate(event)) return false;
        if (!this.checkSearch(event)) return false;
        
        // Новые фильтры
        if (!this.checkRadius(event)) return false;
        if (!this.checkRating(event)) return false;
        if (!this.checkParticipants(event)) return false;
        
        return true;
    }

    checkRadius(event) {
        if (!this.options.filters.radius || !this.userLocation) return true;
        
        const distance = this.calculateDistance(
            this.userLocation[0],
            this.userLocation[1],
            event.latitude,
            event.longitude
        );
        
        return distance <= this.options.filters.radius;
    }

    checkRating(event) {
        if (!this.options.filters.rating) return true;
        return (event.average_rating || 0) >= this.options.filters.rating;
    }

    checkParticipants(event) {
        if (!this.options.filters.participants) return true;
        return (event.registrations_count || 0) >= this.options.filters.participants;
    }

    checkCategory(event) {
        const selectedCategory = document.getElementById('category-filter')?.value;
        return !selectedCategory || selectedCategory === 'all' || event.category === selectedCategory;
    }

    checkPrice(event) {
        const selectedPrice = document.getElementById('price-filter')?.value;
        if (!selectedPrice || selectedPrice === 'all') return true;
        
        switch (selectedPrice) {
            case 'free': return event.price === 0;
            case 'paid': return event.price > 0;
            default: return true;
        }
    }

    checkDate(event) {
        const selectedDate = document.getElementById('date-filter')?.value;
        if (!selectedDate || selectedDate === 'all') return true;
        
        const eventDate = new Date(event.start_date || event.date);
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
            default:
                return true;
        }
    }

    checkSearch(event) {
        const searchTerm = document.getElementById('map-search')?.value.toLowerCase();
        if (!searchTerm) return true;
        
        return event.title.toLowerCase().includes(searchTerm) ||
               event.description?.toLowerCase().includes(searchTerm) ||
               event.location.toLowerCase().includes(searchTerm);
    }

    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Радиус Земли в км
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
            Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    updateVisibleStats(visibleCount) {
        const statsElement = document.getElementById('map-stats');
        if (statsElement) {
            statsElement.innerHTML = `
                <div class="map-stats">
                    <span class="stat-item">🗺️ ${visibleCount} видно</span>
                    <span class="stat-item">🎯 ${this.markers.length} всего</span>
                    ${this.userLocation ? `<span class="stat-item">📍 Ваше местоположение</span>` : ''}
                </div>
            `;
        }
    }

    showFallbackMap() {
        this.container.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #666;">
                <h3>⚠️ Карта временно недоступна</h3>
                <p>Попробуйте обновить страницу или зайти позже</p>
                <button onclick="location.reload()" class="btn btn-primary">
                    Обновить страницу
                </button>
            </div>
        `;
    }

    initClusterer() {
        this.clusterer = new ymaps.Clusterer({
            clusterDisableClickZoom: true,
            clusterOpenBalloonOnClick: true,
            clusterBalloonContentLayout: 'cluster#balloonCarousel',
            clusterBalloonItemContentLayout: this.createClusterItemLayout(),
            clusterBalloonPanelMaxMapArea: 0,
            clusterBalloonContentLayoutWidth: 300,
            clusterBalloonContentLayoutHeight: 200,
            clusterBalloonPagerSize: 5,
            groupByCoordinates: false,
            clusterIcons: this.getClusterIcons()
        });

        this.map.geoObjects.add(this.clusterer);
    }

    getClusterIcons() {
        return [
            {
                href: '/static/events/img/cluster1.png',
                size: [40, 40],
                offset: [-20, -20]
            },
            {
                href: '/static/events/img/cluster2.png', 
                size: [50, 50],
                offset: [-25, -25]
            },
            {
                href: '/static/events/img/cluster3.png',
                size: [60, 60],
                offset: [-30, -30]
            }
        ];
    }
    
    initHeatmap() {
        try {
            // Новая версия API Яндекс.Карт
            this.heatmap = new ymaps.HeatmapLayer(null, {
                radius: 20,
                dissipating: false,
                opacity: 0.6,
                intensityOfMidpoint: 0.2,
                gradient: {
                    0.1: 'rgba(128, 255, 0, 0.3)',
                    0.2: 'rgba(255, 255, 0, 0.5)',
                    0.7: 'rgba(255, 100, 0, 0.7)',
                    1.0: 'rgba(255, 0, 0, 0.9)'
                }
            });

            this.map.geoObjects.add(this.heatmap);
            this.heatmap.options.set('visible', false);
            
        } catch (error) {
            console.error('Error initializing heatmap:', error);
            // Отключаем тепловую карту если не поддерживается
            this.options.heatmapEnabled = false;
        }
    }

    addCustomControls() {
        // Кнопка переключения тепловой карты
        const heatmapToggle = new ymaps.control.Button({
            data: { 
                content: '🔥 Тепловая карта',
                title: 'Показать/скрыть тепловую карту'
            },
            options: { 
                selectOnClick: true,
                maxWidth: 150
            }
        });

        heatmapToggle.events.add('select', () => {
            if (this.heatmap) {
                this.heatmap.options.set('visible', true);
            }
        });

        heatmapToggle.events.add('deselect', () => {
            if (this.heatmap) {
                this.heatmap.options.set('visible', false);
            }
        });

        this.map.controls.add(heatmapToggle, { float: 'right' });

        // Кнопка геолокации
        const geolocationButton = new ymaps.control.Button({
            data: { 
                content: '📍 Мое местоположение',
                title: 'Определить мое местоположение'
            },
            options: { maxWidth: 180 }
        });

        geolocationButton.events.add('press', () => {
            this.locateUser();
        });

        this.map.controls.add(geolocationButton, { float: 'right' });

        // Кнопка сброса
        const resetButton = new ymaps.control.Button({
            data: { 
                content: '🔄 Сбросить',
                title: 'Сбросить карту'
            },
            options: { maxWidth: 100 }
        });

        resetButton.events.add('press', () => {
            this.resetMap();
        });

        this.map.controls.add(resetButton, { float: 'right' });
    }

    // ОБНОВЛЕННАЯ ФУНКЦИОНАЛЬНОСТЬ: Геолокация с фильтрацией по радиусу
    locateUser() {
        if (!navigator.geolocation) {
            alert('Геолокация не поддерживается вашим браузером');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                this.userLocation = [
                    position.coords.latitude,
                    position.coords.longitude
                ];

                // Удаляем старый маркер местоположения
                if (this.userPlacemark) {
                    this.map.geoObjects.remove(this.userPlacemark);
                }

                this.userPlacemark = new ymaps.Placemark(this.userLocation, {
                    balloonContent: 'Ваше местоположение'
                }, {
                    preset: 'islands#blueCircleIcon',
                    draggable: false
                });

                this.map.geoObjects.add(this.userPlacemark);
                this.map.setCenter(this.userLocation, 13);

                // Устанавливаем фильтр по радиусу
                this.options.filters.radius = 10;
                const radiusSlider = document.getElementById('radius-filter');
                const radiusValue = document.getElementById('radius-value');
                if (radiusSlider && radiusValue) {
                    radiusSlider.value = 10;
                    radiusValue.textContent = '10 км';
                }

                this.applyFilters();
                this.showNotification('Ваше местоположение определено! Показаны мероприятия в радиусе 10 км', 'success');
            },
            (error) => {
                console.error('Geolocation error:', error);
                let errorMessage = 'Не удалось определить ваше местоположение';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Доступ к геолокации запрещен. Разрешите доступ в настройках браузера.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Информация о местоположении недоступна.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Время ожидания определения местоположения истекло.';
                        break;
                }
                this.showNotification(errorMessage, 'error');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    }

    resetMap() {
        this.map.setCenter(this.options.center, this.options.zoom);
        if (this.filters) {
            this.filters.resetFilters();
        }
        
        // Сбрасываем фильтр радиуса
        this.options.filters.radius = null;
        const radiusSlider = document.getElementById('radius-filter');
        const radiusValue = document.getElementById('radius-value');
        if (radiusSlider && radiusValue) {
            radiusSlider.value = 0;
            radiusValue.textContent = 'Любой';
        }
        
        // Удаляем маркер местоположения
        if (this.userPlacemark) {
            this.map.geoObjects.remove(this.userPlacemark);
            this.userPlacemark = null;
            this.userLocation = null;
        }
        
        this.loadEvents();
    }

    async showNearestEvents(userLocation) {
        try {
            const response = await fetch(`/api/events/nearby/?lat=${userLocation[0]}&lon=${userLocation[1]}&radius=10`);
            const events = await response.json();

            events.forEach(event => {
                this.addEventMarker(event, true);
            });
        } catch (error) {
            console.error('Error loading nearby events:', error);
        }
    }

    createClusterItemLayout() {
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
        const badges = event.badges && event.badges.length > 0 ? 
            event.badges.map(badge => `<span class="badge badge-${badge}">${this.getBadgeText(badge)}</span>`).join('') : 
            '';
        
        const date = new Date(event.start_date || event.date).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Добавляем информацию о рейтинге и участниках
        const ratingInfo = event.average_rating ? 
            `<p><strong>⭐ Рейтинг:</strong> ${event.average_rating.toFixed(1)}</p>` : '';
        
        const participantsInfo = event.registrations_count ? 
            `<p><strong>👥 Участников:</strong> ${event.registrations_count}</p>` : '';

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
                    ${ratingInfo}
                    ${participantsInfo}
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
            // Если данные уже переданы в options, используем их
            if (this.options.eventsData && Array.isArray(this.options.eventsData)) {
                console.log('Using preloaded events data:', this.options.eventsData.length);
                this.renderEvents(this.options.eventsData);
                return;
            }

            // Иначе загружаем через API
            const response = await fetch('/api/events/?format=json&map=true');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const events = await response.json();
            
            if (!Array.isArray(events)) {
                throw new Error('Events data is not an array');
            }
            
            this.renderEvents(events);
            
        } catch (error) {
            console.error('Error loading events:', error);
            this.showError('Не удалось загрузить мероприятия');
            // Показываем тестовые данные
            this.showTestData();
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-warning';
        errorDiv.style.cssText = `
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            min-width: 300px;
            text-align: center;
        `;
        errorDiv.textContent = message;
        this.container.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    renderEvents(events) {
        console.log('Rendering events:', events);
        
        if (!Array.isArray(events)) {
            console.error('Events is not an array:', events);
            this.showTestData();
            return;
        }

        if (this.clusterer) {
            this.clusterer.removeAll();
        }
        this.markers = [];

        let addedCount = 0;
        events.forEach(event => {
            if (event.latitude && event.longitude) {
                this.addEventMarker(event);
                addedCount++;
            } else {
                console.warn('Event missing coordinates:', event.title);
            }
        });

        console.log(`Added ${addedCount} markers from ${events.length} events`);
        this.updateEventsStats(events);
        
        // Обновляем тепловую карту
        if (this.heatmap) {
            this.updateHeatmap(events);
        }
    }

    showTestData() {
        console.log('Showing test data');
        const testEvents = [
            {
                id: 1,
                title: 'Тестовое мероприятие 1',
                latitude: 55.76,
                longitude: 37.64,
                location: 'Москва, Красная площадь',
                price: 0,
                category_name: 'Тест',
                organizer_name: 'Система',
                short_description: 'Тестовое мероприятие для демонстрации',
                average_rating: 4.5,
                registrations_count: 25
            },
            {
                id: 2,
                title: 'Тестовое мероприятие 2',
                latitude: 55.75,
                longitude: 37.65,
                location: 'Москва, Кремль',
                price: 1000,
                category_name: 'Тест',
                organizer_name: 'Система',
                short_description: 'Еще одно тестовое мероприятие',
                average_rating: 4.2,
                registrations_count: 50
            }
        ];
        
        this.renderEvents(testEvents);
    }

    addEventMarker(event, isHighlighted = false) {
        const coordinates = [parseFloat(event.latitude), parseFloat(event.longitude)];
        
        console.log('Adding marker:', event.title, coordinates);
        
        const marker = new ymaps.Placemark(coordinates, {
            balloonContent: this.createEventBalloonContent(event),
            hintContent: event.title,
            eventData: event
        }, {
            preset: this.getEventPreset(event),
            balloonCloseButton: true,
            hideIconOnBalloonOpen: false,
            balloonOffset: [0, -40]
        });

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
        if (!this.heatmap || !Array.isArray(events)) return;

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

        // Новая версия API
        if (this.heatmap.setData) {
            this.heatmap.setData(points);
        }
    }

    calculateEventWeight(event) {
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
            today: events.filter(e => this.isToday(e.start_date || e.date)).length
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
        this.trackEventClick(event.id);
        this.showEventDetails(event);
    }

    trackEventView(eventId) {
        fetch(`/api/events/${eventId}/track_view/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json'
            }
        });
    }

    trackEventClick(eventId) {
        fetch(`/api/events/${eventId}/track_click/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json'
            }
        });
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    showEventDetails(event) {
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
        marker.options.set('preset', 'islands#redIcon');
        setTimeout(() => {
            marker.options.set('preset', this.getEventPreset(marker.properties.get('eventData')));
        }, 3000);
    }

    cleanupContainer() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} notification`;
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
        }, 5000);
    }

    destroy() {
        if (this.map) {
            this.map.destroy();
            this.map = null;
        }
        
        if (this.clusterer) {
            this.clusterer.removeAll();
            this.clusterer = null;
        }
        
        this.markers = [];
        this.isInitialized = false;
        
        if (window.activeMaps) {
            delete window.activeMaps[this.container.id];
        }
        
        this.cleanupContainer();
    }
}

// ОБНОВЛЕННЫЙ КЛАСС ДЛЯ ФИЛЬТРОВ
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
        this.setupAdvancedFilters();
    }

    setupAdvancedFilters() {
        // Радиус фильтр
        const radiusSlider = document.getElementById('radius-filter');
        if (radiusSlider) {
            radiusSlider.addEventListener('input', (e) => {
                const radius = parseInt(e.target.value);
                if (radius === 0) {
                    this.activeFilters.delete('radius');
                } else {
                    this.activeFilters.add('radius');
                }
                this.applyFilters();
            });
        }

        // Рейтинг фильтр
        const ratingSelect = document.getElementById('rating-filter');
        if (ratingSelect) {
            ratingSelect.addEventListener('change', (e) => {
                if (e.target.value === 'all') {
                    this.activeFilters.delete('rating');
                } else {
                    this.activeFilters.add('rating');
                }
                this.applyFilters();
            });
        }

        // Участники фильтр
        const participantsSelect = document.getElementById('participants-filter');
        if (participantsSelect) {
            participantsSelect.addEventListener('change', (e) => {
                if (e.target.value === 'all') {
                    this.activeFilters.delete('participants');
                } else {
                    this.activeFilters.add('participants');
                }
                this.applyFilters();
            });
        }
    }

    setupCategoryFilter() {
        const categorySelect = document.getElementById('category-filter');
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => {
                if (e.target.value === 'all') {
                    this.activeFilters.delete('category');
                } else {
                    this.activeFilters.add('category');
                }
                this.applyFilters();
            });
        } else {
            console.warn('Category filter element not found');
        }
    }

    setupPriceFilter() {
        const priceSelect = document.getElementById('price-filter');
        if (priceSelect) {
            priceSelect.addEventListener('change', (e) => {
                if (e.target.value === 'all') {
                    this.activeFilters.delete('price');
                } else {
                    this.activeFilters.add('price');
                }
                this.applyFilters();
            });
        } else {
            console.warn('Price filter element not found');
        }
    }

    setupDateFilter() {
        const dateSelect = document.getElementById('date-filter');
        if (dateSelect) {
            dateSelect.addEventListener('change', (e) => {
                if (e.target.value === 'all') {
                    this.activeFilters.delete('date');
                } else {
                    this.activeFilters.add('date');
                }
                this.applyFilters();
            });
        } else {
            console.warn('Date filter element not found');
        }
    }

    setupSearchFilter() {
        const searchInput = document.getElementById('map-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                if (!e.target.value) {
                    this.activeFilters.delete('search');
                } else {
                    this.activeFilters.add('search');
                }
                this.applyFilters();
            });
        } else {
            console.warn('Search filter element not found');
        }
    }

    applyFilters() {
        if (!this.map.markers) return;
        
        let visibleCount = 0;
        
        this.map.markers.forEach(marker => {
            const event = marker.properties.get('eventData');
            const isVisible = this.isEventVisible(event);
            
            marker.options.set('visible', isVisible);
            
            if (isVisible) {
                visibleCount++;
            }
        });
        
        // Обновляем статистику видимых маркеров
        this.updateVisibleStats(visibleCount);
        
        if (this.map.clusterer) {
            this.map.clusterer.repaint();
        }
    }

    isEventVisible(event) {
        // Проверяем все активные фильтры
        for (let filter of this.activeFilters) {
            if (!this[`check${filter.charAt(0).toUpperCase() + filter.slice(1)}`](event)) {
                return false;
            }
        }
        return true;
    }

    checkRadius(event) {
        const radiusSlider = document.getElementById('radius-filter');
        if (!radiusSlider) return true;
        
        const radius = parseInt(radiusSlider.value);
        if (radius === 0 || !this.map.userLocation) return true;
        
        const distance = this.map.calculateDistance(
            this.map.userLocation[0],
            this.map.userLocation[1],
            event.latitude,
            event.longitude
        );
        
        return distance <= radius;
    }

    checkRating(event) {
        const ratingSelect = document.getElementById('rating-filter');
        if (!ratingSelect) return true;
        
        const minRating = parseFloat(ratingSelect.value);
        if (isNaN(minRating)) return true;
        
        return (event.average_rating || 0) >= minRating;
    }

    checkParticipants(event) {
        const participantsSelect = document.getElementById('participants-filter');
        if (!participantsSelect) return true;
        
        const minParticipants = parseInt(participantsSelect.value);
        if (isNaN(minParticipants)) return true;
        
        return (event.registrations_count || 0) >= minParticipants;
    }

    checkCategory(event) {
        const selectedCategory = document.getElementById('category-filter')?.value;
        return !selectedCategory || selectedCategory === 'all' || event.category === selectedCategory;
    }

    checkPrice(event) {
        const selectedPrice = document.getElementById('price-filter')?.value;
        if (!selectedPrice || selectedPrice === 'all') return true;
        
        switch (selectedPrice) {
            case 'free': return event.price === 0;
            case 'paid': return event.price > 0;
            default: return true;
        }
    }

    checkDate(event) {
        const selectedDate = document.getElementById('date-filter')?.value;
        if (!selectedDate || selectedDate === 'all') return true;
        
        const eventDate = new Date(event.start_date || event.date);
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
            default:
                return true;
        }
    }

    checkSearch(event) {
        const searchTerm = document.getElementById('map-search')?.value.toLowerCase();
        if (!searchTerm) return true;
        
        return event.title.toLowerCase().includes(searchTerm) ||
            event.description?.toLowerCase().includes(searchTerm) ||
            event.location.toLowerCase().includes(searchTerm);
    }

    updateVisibleStats(visibleCount) {
        const statsElement = document.getElementById('map-stats');
        if (statsElement) {
            statsElement.innerHTML = `
                <div class="map-stats">
                    <span class="stat-item">🗺️ ${visibleCount} видно</span>
                    <span class="stat-item">🎯 ${this.map.markers.length} всего</span>
                    ${this.map.userLocation ? `<span class="stat-item">📍 Ваше местоположение</span>` : ''}
                </div>
            `;
        }
    }

    resetFilters() {
        this.activeFilters.clear();
        
        // Сбрасываем все элементы фильтров
        const filterElements = [
            'category-filter', 'price-filter', 'date-filter', 'map-search',
            'radius-filter', 'rating-filter', 'participants-filter'
        ];
        
        filterElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                if (element.type === 'range') {
                    element.value = 0;
                } else if (element.type === 'text') {
                    element.value = '';
                } else {
                    element.value = 'all';
                }
            }
        });
        
        // Обновляем отображение радиуса
        const radiusValue = document.getElementById('radius-value');
        if (radiusValue) {
            radiusValue.textContent = 'Любой';
        }
        
        this.applyFilters();
    }
    }

    // Функции для мини-карт на других страницах
    class MiniEventMap {
        constructor(containerId, options = {}) {
            this.container = document.getElementById(containerId);
            this.options = {
                center: [55.76, 37.64],
                zoom: 10,
                ...options
            };
            this.init();
        }

        async init() {
            await this.loadYmaps();
            this.initMap();
            this.loadEvents();
        }

        loadYmaps() {
            return new Promise((resolve) => {
                if (window.ymaps) {
                    ymaps.ready(resolve);
                    return;
                }
                
                const script = document.createElement('script');
                script.src = `https://api-maps.yandex.ru/2.1/?apikey=${this.options.apiKey || 'your-api-key'}&lang=ru_RU`;
                script.onload = () => ymaps.ready(resolve);
                document.head.appendChild(script);
            });
        }

        initMap() {
            ymaps.ready(() => {
                this.map = new ymaps.Map(this.container, {
                    center: this.options.center,
                    zoom: this.options.zoom,
                    controls: ['zoomControl', 'typeSelector']
                });
            });
        }

        async loadEvents() {
            try {
                const response = await fetch('/api/events/map/?limit=10');
                const events = await response.json();
                
                if (Array.isArray(events)) {
                    this.renderEvents(events);
                }
            } catch (error) {
                console.error('Error loading events for mini map:', error);
            }
        }

        renderEvents(events) {
            if (!this.map) return;

            events.forEach(event => {
                if (event.latitude && event.longitude) {
                    const placemark = new ymaps.Placemark(
                        [event.latitude, event.longitude],
                        {
                            balloonContent: `
                                <div class="mini-event-balloon">
                                    <h5>${event.title}</h5>
                                    <p>${event.location}</p>
                                    <a href="${event.url}" class="btn btn-primary btn-sm">Подробнее</a>
                                </div>
                            `,
                            hintContent: event.title
                        },
                        {
                            preset: 'islands#blueEventIcon'
                        }
                    );

                    this.map.geoObjects.add(placemark);
                }
            });
        }
    }

    // Глобальные функции
    let globalEventMap = null;

    function initEventMap(containerId = 'map', options = {}) {
        if (globalEventMap) {
            globalEventMap.destroy();
            globalEventMap = null;
        }
        
        setTimeout(() => {
            try {
                globalEventMap = new EnhancedEventMap(containerId, options);
                window.eventMap = globalEventMap;
            } catch (error) {
                console.error('Failed to initialize map:', error);
            }
        }, 100);
    }

    function initMiniMap(containerId = 'mini-map', options = {}) {
        return new MiniEventMap(containerId, options);
    }

    function initEventDetailMap(containerId = 'event-map', eventData = {}) {
        if (!eventData.latitude || !eventData.longitude) return;
        
        ymaps.ready(() => {
            const map = new ymaps.Map(containerId, {
                center: [eventData.latitude, eventData.longitude],
                zoom: 15,
                controls: ['zoomControl']
            });
            
            const placemark = new ymaps.Placemark(
                [eventData.latitude, eventData.longitude],
                {
                    balloonContent: `
                        <h5>${eventData.title || 'Мероприятие'}</h5>
                        <p>${eventData.location || ''}</p>
                    `
                },
                {
                    preset: 'islands#redIcon'
                }
            );
            
            map.geoObjects.add(placemark);
            placemark.balloon.open();
        });
    }

    function destroyEventMap() {
        if (globalEventMap) {
            globalEventMap.destroy();
            globalEventMap = null;
            window.eventMap = null;
        }
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
        })
        .catch(error => {
            console.error('Error adding to favorites:', error);
            showNotification('Ошибка при добавлении в избранное', 'error');
        });
    }

    function registerForEvent(eventId) {
        window.location.href = `/event/${eventId}/register/`;
    }

    function getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    function showNotification(message, type = 'info') {
        // Удаляем существующие уведомления
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} notification`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            min-width: 300px;
            max-width: 400px;
            word-wrap: break-word;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Автоматическая инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        // Основная карта мероприятий
        if (document.getElementById('map')) {
            const apiKey = document.getElementById('map').dataset.apiKey;
            const eventsData = window.eventsData || [];
            
            initEventMap('map', {
                apiKey: apiKey,
                eventsData: eventsData,
                clusteringEnabled: true,
                heatmapEnabled: true
            });
        }
        
        // Мини-карта на главной странице
        if (document.getElementById('mini-map')) {
            initMiniMap('mini-map', {
                zoom: 11,
                center: [55.76, 37.64]
            });
        }
        
        // Карта на странице мероприятия
        if (document.getElementById('event-map')) {
            const eventMap = document.getElementById('event-map');
            const eventData = {
                latitude: parseFloat(eventMap.dataset.lat),
                longitude: parseFloat(eventMap.dataset.lon),
                title: eventMap.dataset.title,
                location: eventMap.dataset.location
            };
            
            if (eventData.latitude && eventData.longitude) {
                initEventDetailMap('event-map', eventData);
            }
        }
        
        // Карта на странице поиска
        if (document.getElementById('search-map')) {
            const searchEvents = window.searchEvents || [];
            initEventMap('search-map', {
                eventsData: searchEvents,
                clusteringEnabled: true,
                zoom: 12
            });
        }
    });

    // Экспорт для использования в других модулях
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            EnhancedEventMap,
            MiniEventMap,
            initEventMap,
            initMiniMap,
            initEventDetailMap
        };
    }
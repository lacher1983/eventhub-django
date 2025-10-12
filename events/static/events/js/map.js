class EventFilters {
    constructor(mapInstance) {
        this.map = mapInstance;
        this.initFilters();
    }

    initFilters() {
        // Логика фильтрации маркеров
        document.getElementById('category-filter').addEventListener('change', (e) => {
            this.filterMarkers(e.target.value);
        });
    }

    filterMarkers(category) {
        this.map.markers.forEach(marker => {
            const eventCategory = marker.properties.get('category');
            if (category === 'all' || eventCategory === category) {
                marker.options.set('visible', true);
            } else {
                marker.options.set('visible', false);
            }
        });
    }
}

// Расширенная версия с кластеризацией
class ClusterEventMap extends EventMap {
    initYandexMap() {
        this.map = new ymaps.Map(this.container, {
            center: [55.76, 37.64],
            zoom: 10
        });

        // Создаем кластеризатор
        this.clusterer = new ymaps.Clusterer({
            clusterDisableClickZoom: true,
            clusterOpenBalloonOnClick: true,
        });

        this.map.geoObjects.add(this.clusterer);
        this.loadEvents();
    }

    addEventMarker(event) {
        const marker = new ymaps.Placemark(
            [event.latitude, event.longitude],
            {
                balloonContent: this.createBalloonContent(event),
                hintContent: event.title
            },
            {
                iconLayout: 'default#image',
                iconImageHref: '/static/events/img/marker.png',
                iconImageSize: [40, 40],
            }
        );

        this.clusterer.add(marker);
        this.markers.push(marker);
    }

    createBalloonContent(event) {
        return `
            <div class="event-balloon">
                <h4>${event.title}</h4>
                <p><strong>Дата:</strong> ${new Date(event.date).toLocaleDateString()}</p>
                <p><strong>Место:</strong> ${event.location}</p>
                <a href="/events/${event.id}/" class="btn btn-primary btn-sm">Подробнее</a>
            </div>
        `;
    }
}
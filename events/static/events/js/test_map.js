console.log('=== TEST MAP SCRIPT LOADED ===');

function initTestMap() {
    console.log('=== INIT TEST MAP ===');
    
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('Map container not found!');
        return;
    }

    if (typeof ymaps === 'undefined') {
        console.error('Yandex Maps not loaded!');
        mapContainer.innerHTML = `
            <div class="alert alert-danger m-3">
                <h4>❌ Яндекс.Карты не загружены</h4>
                <p>Проверьте:</p>
                <ul>
                    <li>API ключ в настройках</li>
                    <li>Подключение к интернету</li>
                    <li>Консоль браузера для ошибок</li>
                </ul>
                <button onclick="location.reload()" class="btn btn-primary">Обновить страницу</button>
            </div>
        `;
        return;
    }

    console.log('Yandex Maps loaded, initializing...');

    ymaps.ready(function() {
        try {
            // Очищаем контейнер
            mapContainer.innerHTML = '';
            
            // Создаем карту
            const map = new ymaps.Map('map', {
                center: [55.76, 37.64],
                zoom: 10,
                controls: ['zoomControl', 'fullscreenControl']
            });

            console.log('Map created successfully!');

            // Добавляем тестовые маркеры
            const testMarkers = [
                { coords: [55.76, 37.64], title: 'Тест 1 - Красная площадь' },
                { coords: [55.75, 37.65], title: 'Тест 2 - Кремль' },
                { coords: [55.74, 37.63], title: 'Тест 3 - Парк' }
            ];

            testMarkers.forEach((marker, index) => {
                const placemark = new ymaps.Placemark(marker.coords, {
                    balloonContent: `<strong>${marker.title}</strong><br>Это тестовый маркер №${index + 1}`
                }, {
                    preset: 'islands#redIcon'
                });

                map.geoObjects.add(placemark);
            });

            console.log('Test markers added');

            // Добавляем кнопку геолокации
            const geolocationButton = new ymaps.control.Button({
                data: { content: '📍 Мое местоположение' },
                options: { maxWidth: 200 }
            });

            geolocationButton.events.add('press', function() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                        const userCoords = [position.coords.latitude, position.coords.longitude];
                        map.setCenter(userCoords, 15);
                        
                        const userMarker = new ymaps.Placemark(userCoords, {
                            balloonContent: 'Ваше местоположение'
                        }, {
                            preset: 'islands#blueCircleIcon'
                        });
                        
                        map.geoObjects.add(userMarker);
                    });
                } else {
                    alert('Геолокация не поддерживается вашим браузером');
                }
            });

            map.controls.add(geolocationButton, { float: 'right' });

            console.log('=== TEST MAP INITIALIZED SUCCESSFULLY ===');

        } catch (error) {
            console.error('Error creating map:', error);
            mapContainer.innerHTML = `
                <div class="alert alert-danger m-3">
                    <h4>❌ Ошибка создания карты</h4>
                    <p>${error.message}</p>
                    <button onclick="location.reload()" class="btn btn-primary">Обновить страницу</button>
                </div>
            `;
        }
    });
}

// Автоматически инициализируем при загрузке
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing test map...');
    setTimeout(initTestMap, 100);
});
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    def get_event_weather(self, event):
        """Получение прогноза погоды для мероприятия"""
        cache_key = f"weather_{event.id}_{event.date.strftime('%Y%m%d')}"
        cached_weather = cache.get(cache_key)
        
        if cached_weather:
            return cached_weather
        
        try:
            # Геокодирование локации (упрощенное)
            location = self.geocode_location(event.location)
            if not location:
                return None
            
            # Получение погоды
            url = f"{self.base_url}/forecast"
            params = {
                'lat': location['lat'],
                'lon': location['lon'],
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'ru'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                weather_data = response.json()
                forecast = self.extract_event_forecast(weather_data, event.date)
                
                # Кэшируем на 1 час
                cache.set(cache_key, forecast, 3600)
                return forecast
                
        except Exception as e:
            logger.error(f"Weather API error: {e}")
        
        return None
    
    def geocode_location(self, location):
        """Упрощенное геокодирование (можно заменить на Google Geocoding API)"""
        # База основных городов
        cities = {
            'москва': {'lat': 55.7558, 'lon': 37.6173},
            'санкт-петербург': {'lat': 59.9311, 'lon': 30.3609},
            'новосибирск': {'lat': 55.0084, 'lon': 82.9357},
            'екатеринбург': {'lat': 56.8389, 'lon': 60.6057},
            'казань': {'lat': 55.7961, 'lon': 49.1064},
        }
        
        location_lower = location.lower()
        for city, coords in cities.items():
            if city in location_lower:
                return coords
        
        return None
    
    def extract_event_forecast(self, weather_data, event_date):
        """Извлечение прогноза для даты мероприятия"""
        for forecast in weather_data.get('list', []):
            forecast_date = forecast['dt_txt']
            # Простое сравнение дат (можно улучшить)
            if event_date.strftime('%Y-%m-%d') in forecast_date:
                return {
                    'temperature': forecast['main']['temp'],
                    'description': forecast['weather'][0]['description'],
                    'icon': forecast['weather'][0]['icon'],
                    'humidity': forecast['main']['humidity'],
                    'wind_speed': forecast['wind']['speed']
                }
        return None
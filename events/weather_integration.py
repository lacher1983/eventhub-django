import requests
from django.conf import settings
from django.core.cache import cache
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.geolocator = Nominatim(user_agent="eventhub_app")
    
    def get_event_weather(self, event):
        """Получение прогноза погоды для мероприятия"""
        cache_key = f"weather_{event.id}_{event.date.strftime('%Y%m%d')}"
        cached_weather = cache.get(cache_key)
        
        if cached_weather:
            return cached_weather
        
        try:
            # Улучшенное геокодирование
            location = self.geocode_location(event.location)
            if not location:
                logger.warning(f"Не удалось геокодировать локацию: {event.location}")
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
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                weather_data = response.json()
                forecast = self.extract_event_forecast(weather_data, event.date)
                
                if forecast:
                    # Кэшируем на 1 час
                    cache.set(cache_key, forecast, 3600)
                    return forecast
                else:
                    logger.warning(f"Не найден прогноз для даты {event.date}")
                    
        except requests.exceptions.Timeout:
            logger.error("Timeout при запросе к Weather API")
        except Exception as e:
            logger.error(f"Weather API error: {e}")
        
        return None
    
    def geocode_location(self, location):
        """Улучшенное геокодирование"""
        try:
            # Сначала пробуем нашу базу городов
            city_coords = self._get_city_coordinates(location)
            if city_coords:
                return city_coords
            
            # Если не нашли, используем внешний сервис
            time.sleep(1)  # Чтобы не превысить лимиты
            geo_location = self.geolocator.geocode(location, country_codes='ru', language='ru')
            
            if geo_location:
                return {
                    'lat': geo_location.latitude,
                    'lon': geo_location.longitude,
                    'address': geo_location.address
                }
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error for {location}: {e}")
        
        return None
    
    def _get_city_coordinates(self, location):
        """Расширенная база координат городов"""
        cities = {
            'москва': {'lat': 55.7558, 'lon': 37.6173},
            'санкт-петербург': {'lat': 59.9311, 'lon': 30.3609},
            'новосибирск': {'lat': 55.0084, 'lon': 82.9357},
            'екатеринбург': {'lat': 56.8389, 'lon': 60.6057},
            'казань': {'lat': 55.7961, 'lon': 49.1064},
            'нижний новгород': {'lat': 56.3269, 'lon': 44.0059},
            'челябинск': {'lat': 55.1644, 'lon': 61.4368},
            'самара': {'lat': 53.1959, 'lon': 50.1002},
            'омск': {'lat': 54.9924, 'lon': 73.3686},
            'ростов-на-дону': {'lat': 47.2224, 'lon': 39.7186},
            'уфа': {'lat': 54.7351, 'lon': 55.9587},
            'красноярск': {'lat': 56.0153, 'lon': 92.8932},
            'пермь': {'lat': 58.0105, 'lon': 56.2502},
            'воронеж': {'lat': 51.6615, 'lon': 39.2003},
            'волгоград': {'lat': 48.7080, 'lon': 44.5133},
        }
        
        location_lower = location.lower().strip()
        for city, coords in cities.items():
            if city in location_lower:
                return coords
        
        return None
    
    def extract_event_forecast(self, weather_data, event_date):
        """Улучшенное извлечение прогноза"""
        event_date_str = event_date.strftime('%Y-%m-%d')
        
        for forecast in weather_data.get('list', []):
            forecast_datetime = forecast['dt_txt']
            forecast_date = forecast_datetime.split(' ')[0]
            
            if event_date_str == forecast_date:
                # Берем прогноз на 12:00 дня мероприятия
                forecast_time = forecast_datetime.split(' ')[1]
                if forecast_time.startswith('12:00') or len(weather_data.get('list', [])) <= 8:
                    return {
                        'temperature': forecast['main']['temp'],
                        'feels_like': forecast['main']['feels_like'],
                        'description': forecast['weather'][0]['description'],
                        'icon': forecast['weather'][0]['icon'],
                        'humidity': forecast['main']['humidity'],
                        'wind_speed': forecast['wind']['speed'],
                        'pressure': forecast['main']['pressure'],
                        'clouds': forecast['clouds']['all']
                    }
        
        # Если не нашли точное время, берем первый доступный прогноз на нужную дату
        for forecast in weather_data.get('list', []):
            forecast_date = forecast['dt_txt'].split(' ')[0]
            if event_date_str == forecast_date:
                return {
                    'temperature': forecast['main']['temp'],
                    'feels_like': forecast['main']['feels_like'],
                    'description': forecast['weather'][0]['description'],
                    'icon': forecast['weather'][0]['icon'],
                    'humidity': forecast['main']['humidity'],
                    'wind_speed': forecast['wind']['speed'],
                    'pressure': forecast['main']['pressure'],
                    'clouds': forecast['clouds']['all']
                }
        
        return None
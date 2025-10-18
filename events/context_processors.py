from django.utils import timezone
from .models import Advertisement
from .models import Cart
from .models import Category, Event


def event_filters(request):
    return {
        'categories': Category.objects.all(),
        'event_types': Event.EVENT_TYPES,
    }

def advertisements(request):
    now = timezone.now()
    active_ads = Advertisement.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    )
    
    ads_by_position = {}
    for position in dict(Advertisement.POSITIONS).keys():
        ads_by_position[position] = active_ads.filter(position=position)
    
    return {
        'advertisements': ads_by_position,
    }

from .models import Cart

def cart_context(request):
    """Добавляет количество товаров в корзине в контекст всех шаблонов"""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items_count = cart.items.count()
        except Cart.DoesNotExist:
            cart_items_count = 0
    else:
        cart_items_count = 0
    
    return {
        'cart_items_count': cart_items_count
    }

def map_pages(request):
    """Определяет, на каких страницах нужны Яндекс.Карты"""
    map_url_names = [
        'events_map',  # страница карты мероприятий
        'event_detail', # детальная страница события (если есть мини-карта)
        'event_create', # создание события (если есть карта)
        'event_edit',   # редактирование события
        'event_list',
    ]
    
    current_url_name = request.resolver_match.url_name if request.resolver_match else None
    
    return {
        'map_pages': map_url_names,
        'current_url_needs_map': current_url_name in map_url_names,
    }
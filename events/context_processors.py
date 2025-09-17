from django.utils import timezone
from .models import Advertisement
from .models import Cart

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
    """Добавляет информацию о корзине в контекст всех шаблонов"""
    cart = None    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    
    return {
        'cart': cart, 
        'cart_items_count': cart.items_count if cart else 0, 
        'cart_total_price': cart.total_price if cart else 0
    }

def background_video(request):
    try:
        # Ищем мероприятие с фоновым видео
        background_event = Event.objects.filter(
            is_background_video=True,
            video_trailer__isnull=False
        ).first()
        
        return {
            'background_video': background_event.video_trailer.url if background_event else None,
            'background_event': background_event
        }
    except:
        return {'background_video': None, 'background_event': None}
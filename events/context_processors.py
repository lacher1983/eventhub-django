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
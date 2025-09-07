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
    """
    Контекстный процессор для добавления информации о корзине во все шаблоны
    """
    context = {
        'cart_items_count': 0,
        'cart_total_price': 0
    }
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return {'cart': cart}
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=request.user)
            return {'cart': cart}
    return {'cart': None}
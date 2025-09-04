from django.utils import timezone
from .models import Advertisement

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
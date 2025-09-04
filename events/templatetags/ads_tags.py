from django import template
from django.utils import timezone
from ..models import Advertisement

register = template.Library()

@register.inclusion_tag('events/ads/banner.html')
def show_banner(position, limit=1):
    now = timezone.now()
    banners = Advertisement.objects.filter(
        position=position,
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    )[:limit]

    print(f"DEBUG: show_banner('{position}') найдено: {banners.count()}")
    
    return {'banners': banners}

@register.inclusion_tag('events/ads/video.html')  
def show_video_ad():
    now = timezone.now()
    video_ads = Advertisement.objects.filter(
        ad_type='video',
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).first()
    
    print(f"DEBUG: show_video_ad() найдено: {1 if video_ads else 0}")
    
    return {'video_ad': video_ads}
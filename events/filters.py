import django_filters
from .models import Event

class EventFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    date_after = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_before = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    
    class Meta:
        model = Event
        fields = ['category', 'event_type', 'price_min', 'price_max', 'date_after', 'date_before']
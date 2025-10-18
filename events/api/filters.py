from django_filters import rest_framework as filters
from ..models import Event

class EventFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    event_type = filters.ChoiceFilter(choices=Event.EVENT_TYPES)
    date_from = filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='date', lookup_expr='lte')
    location = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Event
        fields = ['title', 'event_type', 'location']
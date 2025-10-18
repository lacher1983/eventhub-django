import django_filters
from .models import Event, Category

class EventFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())

    nearby = django_filters.MethodFilter()

    def filter_nearby(self, queryset, name, value):
        if not value:
            return queryset
        lat, lon = map(float, value.split(','))
        from geopy.distance import distance
        ids = []
        for event in queryset:
            if event.latitude and event.longitude:
                d = distance((lat, lon), (event.latitude, event.longitude)).km
                if d <= 10:  # 10 км
                    ids.append(event.id)
        return queryset.filter(id__in=ids)

    class Meta:
        model = Event
        fields = ['title', 'event_type', 'event_format', 'is_free', 'category']
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from .models import Event
import json
from datetime import datetime, timedelta

class InteractiveCalendarView(TemplateView):
    template_name = 'events/interactive_calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events_json'] = self.get_events_json()
        return context
    
    def get_events_json(self):
        events = Event.objects.filter(
            is_active=True,
            date__gte=timezone.now() - timedelta(days=30)
        ).select_related('category', 'organizer')
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'start': event.date.isoformat(),
                'end': (event.date + timedelta(hours=2)).isoformat(),
                'url': f'/event/{event.id}/',
                'className': f'event-category-{event.category}',
                'extendedProps': {
                    'category': event.get_category_display(),
                    'price': str(event.price),
                    'location': event.location,
                    'organizer': event.organizer.username
                }
            })
        
        return json.dumps(events_data)

def calendar_events_api(request):
    """API для календаря"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    events = Event.objects.filter(is_active=True)
    
    if start and end:
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        events = events.filter(date__range=[start_date, end_date])
    
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'start': event.date.isoformat(),
            'end': (event.date + timedelta(hours=2)).isoformat(),
            'url': f'/event/{event.id}/',
            'color': self.get_category_color(event.category),
        })
    
    return JsonResponse(events_data, safe=False)
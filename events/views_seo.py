from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db.models import Q
import json

class SEOEventListView(ListView):
    """SEO-оптимизированный список мероприятий"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # SEO мета-данные
        context['meta_title'] = "Мероприятия и события | EventHub"
        context['meta_description'] = (
            "Найдите интересные мероприятия, концерты, выставки и встречи в вашем городе. "
            "Бесплатная регистрация, отзывы участников, удобный поиск."
        )
        context['canonical_url'] = self.request.build_absolute_uri()
        
        # Structured data для страницы
        context['structured_data'] = self.get_structured_data()
        
        return context
    
    def get_structured_data(self):
        """Генерация structured data для списка мероприятий"""
        structured_data = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Список мероприятий",
            "description": "Актуальные мероприятия и события",
            "numberOfItems": self.get_queryset().count(),
            "itemListElement": []
        }
        
        for i, event in enumerate(self.get_queryset()[:10], 1):
            event_data = {
                "@type": "ListItem",
                "position": i,
                "item": {
                    "@type": "Event",
                    "name": event.title,
                    "description": event.short_description,
                    "startDate": event.date.isoformat(),
                    "endDate": (event.date + timezone.timedelta(hours=2)).isoformat(),
                    "location": {
                        "@type": "Place",
                        "name": event.location
                    }
                }
            }
            structured_data["itemListElement"].append(event_data)
        
        return json.dumps(structured_data, ensure_ascii=False)

class SEOEventDetailView(DetailView):
    """SEO-оптимизированная детальная страница мероприятия"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        
        # Динамические meta-теги
        context['meta_title'] = f"{event.title} | {event.date.strftime('%d.%m.%Y')} | EventHub"
        context['meta_description'] = self.generate_meta_description(event)
        context['canonical_url'] = self.request.build_absolute_uri()
        
        # Open Graph данные
        context['og_image'] = self.get_og_image(event)
        context['structured_data'] = self.get_event_structured_data(event)
        
        # Breadcrumbs
        context['breadcrumbs'] = [
            {'name': 'Главная', 'url': '/'},
            {'name': 'Мероприятия', 'url': '/events/'},
            {'name': event.title, 'url': event.get_absolute_url()}
        ]
        
        return context
    
    def generate_meta_description(self, event):
        """Генерация meta description для мероприятия"""
        base_description = f"Мероприятие {event.title} состоится {event.date.strftime('%d.%m.%Y')}"
        if event.short_description:
            return f"{base_description}. {event.short_description[:120]}..."
        return base_description
    
    def get_og_image(self, event):
        """Получение изображения для Open Graph"""
        if event.image:
            return self.request.build_absolute_uri(event.image.url)
        return self.request.build_absolute_uri('/static/images/event-default.jpg')
    
    def get_event_structured_data(self, event):
        """Генерация structured data для мероприятия"""
        structured_data = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": event.title,
            "description": event.description or event.short_description,
            "startDate": event.date.isoformat(),
            "endDate": (event.date + timezone.timedelta(hours=event.duration)).isoformat() if event.duration else (event.date + timezone.timedelta(hours=2)).isoformat(),
            "location": {
                "@type": "Place",
                "name": event.location,
                "address": event.address
            },
            "organizer": {
                "@type": "Organization",
                "name": event.organizer.name if event.organizer else "EventHub"
            }
        }
        
        if event.image:
            structured_data["image"] = self.request.build_absolute_uri(event.image.url)
        
        if event.price:
            structured_data["offers"] = {
                "@type": "Offer",
                "price": str(event.price),
                "priceCurrency": "RUB",
                "url": self.request.build_absolute_uri()
            }
        
        return json.dumps(structured_data, ensure_ascii=False)
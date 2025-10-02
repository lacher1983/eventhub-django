from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg
from django_filters import FilterSet, CharFilter, NumberFilter, ChoiceFilter, DateFilter
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Event, Category, Registration, Advertisement, Favorite, Review
from .forms import EventForm, RegistrationForm, ReviewForm, EventFilterForm, CustomUserCreationForm
import json
from django.utils.translation import gettext as _
from django.contrib.auth import login, logout
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder

# Подтверждение email
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailConfirmation

# Обработка исключений
from django.db import DatabaseError
from django.http import Http404

# Используем кастомную модель пользователя
User = get_user_model()

# ==================== РЕКЛАМНЫЕ ФУНКЦИИ ====================
@require_POST
@csrf_exempt
def ad_click(request, ad_id):
    """Обработка клика по рекламе"""
    try:
        ad = Advertisement.objects.get(id=ad_id)
        ad.increment_click()
        return JsonResponse({'status': 'success'})
    except Advertisement.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


@require_POST
@csrf_exempt
def ad_impression(request, ad_id):
    """Обработка показа рекламы"""
    try:
        ad = Advertisement.objects.get(id=ad_id)
        ad.increment_impression()
        return JsonResponse({'status': 'success'})
    except Advertisement.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


# ==================== КЛАССЫ ПРЕДСТАВЛЕНИЙ ====================
class EventListView(ListView):
    """Список активных мероприятий с улучшенным контекстом"""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12

    def get_queryset(self):
        queryset = Event.objects.filter(is_active=True).select_related('organizer')
        
        print("=== DEBUG FILTERS ===")
        print(f"Initial queryset count: {queryset.count()}")

        # Получаем параметры фильтрации
        category = self.request.GET.get('category', '')
        event_type = self.request.GET.get('event_type', '')
        event_format = self.request.GET.get('event_format', '')
        difficulty_level = self.request.GET.get('difficulty_level', '')
        price_type = self.request.GET.get('price_type', '')
        search_query = self.request.GET.get('q', '')

        print(f"Category filter: '{category}'")
        print(f"Event type filter: '{event_type}'")
        print(f"Event format filter: '{event_format}'")
        print(f"Difficulty level filter: '{difficulty_level}'")
        print(f"Price type filter: '{price_type}'")
        print(f"Search query: '{search_query}'")

        # Фильтрация по категории
        if category:
            # Находим ID категории по slug
            try:
                category_obj = Category.objects.get(slug=category)
                queryset = queryset.filter(category=str(category_obj.id))
            except Category.DoesNotExist:
                # Если категория не найдена, возвращаем пустой queryset
                queryset = queryset.none()

        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if event_format:
            queryset = queryset.filter(event_format=event_format)
        if difficulty_level:
            queryset = queryset.filter(difficulty_level=difficulty_level)
        if price_type == 'free':
            queryset = queryset.filter(Q(price=0) | Q(is_free=True))
        elif price_type == 'paid':
            queryset = queryset.filter(price__gt=0, is_free=False)        
        
        # Поиск
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        # Сортировка
        sort = self.request.GET.get('sort', 'date')
        if sort == 'price':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'rating':
            queryset = queryset.order_by('-avg_rating')
        else:
            queryset = queryset.order_by('date')
            
        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем категории в контекст
        context['categories'] = Category.objects.all()

        # Добавляем текущие параметры фильтрации в контекст
        context['current_filters'] = {
            'category': self.request.GET.get('category', ''),
            'event_type': self.request.GET.get('event_type', ''),
            'event_format': self.request.GET.get('event_format', ''),
            'difficulty_level': self.request.GET.get('difficulty_level', ''),
            'price_type': self.request.GET.get('price_type', ''),
            'search': self.request.GET.get('q', ''),
        }
        
        # ИНФОРМАЦИЯ О РЕГИСТРАЦИЯХ
        if self.request.user.is_authenticated:
            # ID мероприятий, на которые пользователь зарегистрирован
            user_registered_ids = Registration.objects.filter(
                user=self.request.user
            ).values_list('event_id', flat=True)
            context['user_registered_events'] = list(user_registered_ids)

            # Отладочная информация
            print(f"User: {self.request.user.username}")
            print(f"Registered events IDs: {list(user_registered_ids)}")
            
            # Помечаем избранные события
            for event in context['events']:
                event.is_favorite = Favorite.objects.filter(
                    user=self.request.user, 
                    event=event
                ).exists()
        else:
            context['user_registered_events'] = []
            print("User is not authenticated")

        return context


class EventDetailView(DetailView):
    """Детальная страница мероприятия"""
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_queryset(self):
        return Event.objects.select_related(
            'organizer'
        ).prefetch_related(
            'reviews', 'reviews__user'
        ).annotate(
            registrations_count=Count('registrations'),
            avg_rating=Avg('reviews__rating')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        
        # Информация о регистрации и избранном
        context['is_registered'] = False
        context['is_favorite'] = False
        context['user_review'] = None
        
        if self.request.user.is_authenticated:
            # Проверка регистрации
            context['is_registered'] = Registration.objects.filter(
                user=self.request.user, event=event
            ).exists()
            
            # Проверка избранного
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user, event=event
            ).exists()
            
            # Отзыв пользователя
            context['user_review'] = Review.objects.filter(
                user=self.request.user, event=event
            ).first()
        
        # Все отзывы о мероприятии
        context['reviews'] = event.reviews.all().select_related('user')
        context['review_form'] = ReviewForm()
        context['available_seats'] = event.capacity - event.registrations_count

        # Используем аннотацию avg_rating
        context['average_rating'] = getattr(event, 'avg_rating', None)

        return context
    
    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Http404:
            raise Http404("Мероприятие не найдено")
        except DatabaseError:
            messages.error(self.request, "Ошибка базы данных")
            return redirect('event_list')

class EventCreateView(LoginRequiredMixin, CreateView):
    """Создание мероприятия"""
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('event_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, _('Мероприятие успешно создано!'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['event_types_json'] = json.dumps(list(Event.EVENT_TYPES))
        # return context
        # Создадим сериализуемый список типов мерпориятий
        event_types = []
        for key, value in Event.EVENT_TYPES:
            try:
                if hasattr(value, '_proxy____text'):
                    label = value._proxy____text
                elif callable(value):
                    label = str(value())
                else:
                    label = str(value)
            except:
                label = str(value)
            
            event_types.append({
                'value': key,
                'label': label
            })
        
        context['event_types_json'] = json.dumps(event_types, cls=TranslationSafeJSONEncoder)

        difficulty_levels = []
        for key, value in Event.DIFFICULTY_LEVELS:
            try:
                if hasattr(value, '_proxy____text'):
                    label = value._proxy____text
                elif callable(value):
                    label = str(value())
                else:
                    label = str(value)
            except:
                label = str(value)
            
            difficulty_levels.append({
                'value': key,
                'label': label
            })
        context['difficulty_levels_json'] = json.dumps(difficulty_levels, cls=TranslationSafeJSONEncoder)
        
        return context

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование мероприятия"""
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Мероприятие успешно обновлено!')
        return super().form_valid(form)

    def test_func(self):
        event = self.get_object()
        return self.request.user == event.organizer

    def get_success_url(self):
        return reverse_lazy('event_detail', kwargs={'pk': self.object.pk})


class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление мероприятия"""
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('event_list')

    def test_func(self):
        event = self.get_object()
        return self.request.user == event.organizer

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Мероприятие успешно удалено!')
        return super().delete(request, *args, **kwargs)


class EventFilter(FilterSet):
    """Фильтр для мероприятий"""
    q = CharFilter(method='search_filter', label='Поиск')
    category = CharFilter(field_name='category__slug', lookup_expr='exact')
    min_price = NumberFilter(field_name='price', lookup_expr='gte')
    max_price = NumberFilter(field_name='price', lookup_expr='lte')
    event_type = ChoiceFilter(choices=Event.EVENT_TYPES)
    start_date = DateFilter(field_name='date', lookup_expr='gte')
    end_date = DateFilter(field_name='date', lookup_expr='lte')
    
    class Meta:
        model = Event
        fields = ['category', 'event_type', 'min_price', 'max_price', 'start_date', 'end_date']
    
    def search_filter(self, queryset, name, value):
        """Поиск по названию и описанию"""
        return queryset.filter(
            Q(title__icontains=value) | 
            Q(description__icontains=value) |
            Q(short_description__icontains=value)
        )


class EventSearchView(ListView):
    """Расширенный поиск мероприятий с фильтрами"""
    model = Event
    template_name = 'events/event_search.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Event.objects.filter(
            is_active=True, 
            date__gte=timezone.now()
        ).select_related('organizer').annotate(
            registrations_count=Count('registrations'),
            average_rating=Avg('reviews__rating')
        )
        
        # Применяем фильтры
        self.filterset = EventFilter(self.request.GET, queryset=queryset)
        
        # Сортировка
        sort_by = self.request.GET.get('sort', 'date')
        if sort_by == 'price':
            return self.filterset.qs.order_by('price')
        elif sort_by == 'price_desc':
            return self.filterset.qs.order_by('-price')
        elif sort_by == 'rating':
            return self.filterset.qs.order_by('-average_rating')
        else:
            return self.filterset.qs.order_by('date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        context['search_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'date')
        context['categories'] = Category.objects.all()
        return context


class OrganizerDashboardView(LoginRequiredMixin, TemplateView):
    """Дашборд организатора"""
    template_name = 'events/dashboard/organizer_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_events = Event.objects.filter(organizer=self.request.user)
        
        context['stats'] = {
            'total_events': user_events.count(),
            'active_events': user_events.filter(is_active=True, date__gte=timezone.now()).count(),
            'past_events': user_events.filter(date__lt=timezone.now()).count(),
            'total_registrations': Registration.objects.filter(
                event__organizer=self.request.user
            ).count(),
        }
        return context


class EventCalendarView(TemplateView):
    """Календарь мероприятий"""
    template_name = 'events/event_calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = Event.objects.filter(
            is_active=True, 
            date__gte=timezone.now()
        )
        return context


class FavoriteListView(LoginRequiredMixin, ListView):
    """Страница с избранными мероприятиями пользователя"""
    model = Favorite
    template_name = 'events/favorite_list.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        # Простой запрос без аннотаций
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('event', 'event__organizer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем дополнительную информацию для каждого избранного мероприятия
        for favorite in context['favorites']:
            # Количество регистраций
            favorite.event.registrations_count = favorite.event.registrations.count()
            
            # Средний рейтинг
            avg_rating = favorite.event.reviews.aggregate(
                avg_rating=Avg('rating')
            )['avg_rating']
            favorite.event.average_rating = avg_rating if avg_rating else 0
            
            # Краткое описание (если пустое)
            if not favorite.event.short_description:
                favorite.event.short_description = "Описание отсутствует"
        
        return context


# ==================== ФУНКЦИИ ДЕКОРАТОРЫ ====================
@require_POST
@login_required
def toggle_favorite(request, event_id):
    """Добавить/удалить мероприятие из избранного (AJAX)"""
    try:
        event = Event.objects.get(id=event_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            event=event
        )
        
        if not created:
            favorite.delete()
            return JsonResponse({'status': 'removed', 'is_favorite': False})
        
        return JsonResponse({'status': 'added', 'is_favorite': True})
        
    except Event.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Мероприятие не найдено'}, status=404)


@login_required
def register_for_event(request, pk):
    """Регистрация на мероприятие"""
    event = get_object_or_404(Event, pk=pk, is_active=True)
    
    if Registration.objects.filter(user=request.user, event=event).exists():
        messages.info(request, 'Вы уже зарегистрированы на это мероприятие')
    elif event.registrations.count() >= event.capacity:
        messages.error(request, 'К сожалению, все места заняты.')
    elif event.date < timezone.now():
        messages.error(request, 'Мероприятие уже прошло.')
    else:
        Registration.objects.create(user=request.user, event=event)
        messages.success(request, 'Вы успешно зарегистрировались на мероприятие!')
    
    return redirect('event_detail', pk=pk)


@login_required
def user_registrations(request):
    """Страница с регистрациями пользователя"""
    registrations = Registration.objects.filter(user=request.user).select_related('event', 'event__organizer')
    return render(request, 'events/user_registrations.html', {
        'registrations': registrations
    })


@login_required
def add_review(request, event_id):
    """Добавление отзыва к мероприятию"""
    event = get_object_or_404(Event, id=event_id)
    
    # Проверяем, был ли пользователь на мероприятии
    if not Registration.objects.filter(user=request.user, event=event).exists():
        messages.error(request, 'Вы должны быть зарегистрированы на мероприятие чтобы оставить отзыв')
        return redirect('event_detail', pk=event_id)
    
    # Проверяем, не оставлял ли уже отзыв
    existing_review = Review.objects.filter(user=request.user, event=event).first()
    if existing_review:
        messages.info(request, 'Вы уже оставляли отзыв на это мероприятие')
        return redirect('event_detail', pk=event_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.event = event
            review.user = request.user
            review.save()
            messages.success(request, 'Ваш отзыв успешно добавлен!')
            return redirect('event_detail', pk=event_id)
    else:
        form = ReviewForm()
    
    return render(request, 'events/add_review.html', {
        'form': form,
        'event': event
    })


@login_required
def edit_review(request, review_id):
    """Редактирование отзыва"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отзыв успешно обновлен!')
            return redirect('event_detail', pk=review.event.id)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'events/edit_review.html', {
        'form': form,
        'review': review
    })

from django.contrib.auth import login


class CustomLogoutView(LogoutView):
    """Кастомный выход из системы"""
    next_page = 'event_list'

    def get(self, request, *args, **kwargs):
        # Разрешаем GET запросы для выхода
        return self.post(request, *args, **kwargs)
    
def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        print("=== ДЕБАГ РЕГИСТРАЦИИ ===")  # Добавим отладочный вывод
        print("Данные формы:", request.POST)
        print("Форма valid:", form.is_valid())
        print("Ошибки формы:", form.errors)

        if form.is_valid():
            user = form.save()

            # Отправляем email подтверждения
            send_confirmation_email(user)
            
            # Автоматически входим после регистрации
            login(request, user)
            
            messages.success(request, f'Регистрация прошла успешно! Добро пожаловать, {user.username}!')
            return redirect('event_list')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
            print("ДЕТАЛЬНЫЕ ОШИБКИ:")
            for field, errors in form.errors.items():
                print(f"Поле {field}: {errors}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'events/register.html', {'form': form})

def custom_logout(request):
    """Кастомный выход из системы"""
    auth_logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('event_list')

def send_confirmation_email(user):
    """Отправка email для подтверждения"""
    confirmation = EmailConfirmation.objects.get(user=user)
    
    subject = 'Подтверждение email на EventHub'
    html_message = render_to_string('events/emails/confirmation_email.html', {
        'user': user,
        'confirmation_code': confirmation.confirmation_code,
        'site_url': 'http://127.0.0.1:8000',  # Замените на ваш домен
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        None,  # Используется DEFAULT_FROM_EMAIL
        [user.email],
        html_message=html_message,
    )

def confirm_email(request, confirmation_code):
    """Подтверждение email"""
    try:
        confirmation = EmailConfirmation.objects.get(
            confirmation_code=confirmation_code,
            confirmed=False
        )
        
        if confirmation.is_expired():
            messages.error(request, 'Ссылка для подтверждения устарела.')
            # Можно отправить новую ссылку
            send_confirmation_email(confirmation.user)
            messages.info(request, 'Новая ссылка отправлена на ваш email.')
        else:
            confirmation.confirmed = True
            confirmation.save()
            messages.success(request, 'Email успешно подтвержден!')
            
    except EmailConfirmation.DoesNotExist:
        messages.error(request, 'Неверная ссылка подтверждения.')
    
    return redirect('event_list')

# Управление подписками
@login_required
def subscription_settings(request):
    """Настройки подписки на уведомления"""
    subscription, created = Subscription.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        selected_categories = request.POST.getlist('categories')
        subscription.categories.set(selected_categories)
        subscription.is_active = bool(selected_categories)
        subscription.save()
        
        messages.success(request, 'Настройки подписки обновлены!')
        return redirect('subscription_settings')
    
    categories = Category.objects.all()
    return render(request, 'events/subscription_settings.html', {
        'subscription': subscription,
        'categories': categories,
    })

@login_required
def notifications(request):
    """Страница уведомлений пользователя"""
    notifications = Notification.objects.filter(
        user=request.user
    ).select_related('event').order_by('-sent_at')
    
    return render(request, 'events/notifications.html', {
        'notifications': notifications,
    })

# Статистика 
@login_required
def event_statistics(request, pk):
    """Статистика конкретного мероприятия"""
    event = get_object_or_404(Event, pk=pk, organizer=request.user)
    
    # Базовая статистика
    stats = {
        'views': event.views_count or 0,
        'registrations': event.registrations.count(),
        'favorites': event.favorited_by.count(),
        'conversion_rate': 0,
    }
    
    if stats['views'] > 0:
        stats['conversion_rate'] = round((stats['registrations'] / stats['views']) * 100, 2)
    
    return render(request, 'events/event_statistics.html', {
        'event': event,
        'stats': stats,
    })

@staff_member_required
def platform_statistics(request):
    """Статистика платформы (только для staff)"""
    today = timezone.now().date()
    
    stats = {
        'total_users': User.objects.count(),
        'total_events': Event.objects.filter(is_active=True).count(),
        'total_registrations': Registration.objects.count(),
        'active_events_today': Event.objects.filter(
            date__date=today,
            is_active=True
        ).count(),
        'new_users_today': User.objects.filter(
            date_joined__date=today
        ).count(),
    }
    
    # Популярные категории
    popular_categories = Category.objects.annotate(
        event_count=Count('event')
    ).order_by('-event_count')[:5]
    
    return render(request, 'events/platform_statistics.html', {
        'stats': stats,
        'popular_categories': popular_categories,
    })

class TranslationSafeJSONEncoder(DjangoJSONEncoder):
    """Кастомный JSON энкодер для обработки translation объектов"""
    def default(self, obj):
        try:
            if hasattr(obj, '_proxy____text'):
                return obj._proxy____text
            elif hasattr(obj, '__html__'):
                return str(obj)
            elif callable(obj):
                return str(obj())
            return super().default(obj)
        except:
            return str(obj)
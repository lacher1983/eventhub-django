from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
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
from .models import Event, ExternalEvent, ExternalEventSource, Category, Registration, Advertisement, Favorite, Review
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
from .models import EmailConfirmation, Subscription, Notification

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

        # Вычисление оставшихся очков до следующего уровня
        if hasattr(self.request.user, 'game_profile') and context.get('next_level'):
            context['points_remaining'] = context['next_level'].min_points - self.request.user.game_profile.total_points
        else:
            context['points_remaining'] = 0
            
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
        # Создадим сериализуемый список типов мероприятий
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
        

class CombinedEventsView(ListView):
    """Объединенное представление внутренних и внешних мероприятий"""
    template_name = 'events/combined_events.html'
    paginate_by = 20
    context_object_name = 'events'
    
    def get_queryset(self):
        # Текущие внутренние мероприятия
        internal_events = Event.objects.filter(
            is_active=True,
            date__gte=timezone.now()
        ).select_related('organizer')
        
        # Текущие внешние мероприятия (не в архиве)
        external_events = ExternalEvent.objects.filter(
            is_archived=False,
            date__gte=timezone.now()
        ).select_related('source')
        
        # Объединяем и сортируем по дате
        combined = []
        
        # Преобразуем внутренние мероприятия
        for event in internal_events:
            combined.append({
                'type': 'internal',
                'object': event,
                'title': event.title,
                'description': event.description,
                'date': event.date,
                'location': event.location,
                'price': event.price,
                'is_free': event.is_free,
                'image_url': event.get_image_url(),
                'category': self._get_event_category(event),  # Используем внутренний метод
                'url': event.get_absolute_url(),
                'source_name': 'EventHub',
                'is_past': False,
            })
        
        # Преобразуем внешние мероприятия
        for event in external_events:
            combined.append({
                'type': 'external',
                'object': event,
                'title': event.title,
                'description': event.description,
                'date': event.date,
                'location': event.location,
                'price': event.price,
                'is_free': event.is_free,
                'image_url': event.image_url,
                'category': event.category,
                'url': event.external_url,
                'source_name': event.source.name,
                'is_past': event.is_past_event,
            })
        
        # Сортируем по дате
        combined.sort(key=lambda x: x['date'])
        return combined
    
    def _get_event_category(self, event):
        """Внутренний метод для получения категории мероприятия"""
        try:
            # Если есть property get_category_display_name
            if hasattr(event, 'get_category_display_name'):
                return event.get_category_display_name
            # Если есть стандартный метод Django get_FOO_display
            elif hasattr(event, 'get_category_display'):
                return event.get_category_display()
            # Просто возвращаем поле category
            elif hasattr(event, 'category'):
                return getattr(event, 'category', 'Не указана')
            else:
                return 'Не указана'
        except Exception:
            return 'Не указана'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Все мероприятия'
        context['current_time'] = timezone.now()
        
        # Статистика
        context['internal_count'] = Event.objects.filter(
            is_active=True, date__gte=timezone.now()
        ).count()
        context['external_count'] = ExternalEvent.objects.filter(
            is_archived=False, date__gte=timezone.now()
        ).count()
        context['total_count'] = context['internal_count'] + context['external_count']
        
        return context


class ArchiveEventsView(ListView):
    """Архив прошедших мероприятий"""
    template_name = 'events/archive.html'
    paginate_by = 20
    context_object_name = 'events'
    
    def get_queryset(self):
        # Архив внутренних мероприятий
        internal_archive = Event.objects.filter(
            Q(is_active=False) | Q(date__lt=timezone.now())
        )
        
        # Архив внешних мероприятий
        external_archive = ExternalEvent.objects.filter(
            is_archived=True
        )
        
        combined = []
        
        for event in internal_archive:
            combined.append({
                'type': 'internal',
                'object': event,
                'title': event.title,
                'date': event.date,
                'location': event.location,
                'is_past': event.date < timezone.now(),
                'source_name': 'EventHub',
            })
        
        for event in external_archive:
            combined.append({
                'type': 'external', 
                'object': event,
                'title': event.title,
                'date': event.date,
                'location': event.location,
                'is_past': True,
                'source_name': event.source.name,
            })

        # Сортируем по дате (сначала самые новые прошедшие)        
        combined.sort(key=lambda x: x['date'], reverse=True)
        return combined
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Архив мероприятий'
        return context
    

class ExternalEventsView(ListView):
    """Только внешние мероприятия"""
    template_name = 'events/external_events.html'
    paginate_by = 20
    context_object_name = 'events'
    
    def get_queryset(self):
        return ExternalEvent.objects.filter(
            is_archived=False,
            date__gte=timezone.now()
        ).select_related('source').order_by('date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Мероприятия с других платформ'
        context['sources'] = ExternalEventSource.objects.filter(is_active=True)
        return context
    

def get_ai_recommended_events(request):
    """Представление для AI-рекомендаций"""
    if request.user.is_authenticated:
        # Для авторизованных - AI рекомендации
        from .ai_recommendations import AIRecommendationEngine
        engine = AIRecommendationEngine()
        recommendations = engine.get_hybrid_recommendations(request.user, 6)
    else:
        # Для неавторизованных - популярные мероприятия
        recommendations = Event.objects.filter(is_active=True).annotate(
            registrations_count=Count('registrations')
        ).order_by('-registrations_count')[:6]
    
    return recommendations

class EventsMapView(TemplateView):
    template_name = "events/events_map.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем активные мероприятия с координатами
        events = Event.objects.filter(
            Q(latitude__isnull=False) & 
            Q(longitude__isnull=False) &
            Q(is_active=True)
        ).select_related('category')
        
        context['events'] = events
        return context


# # ==================== СИСТЕМА ПОПУТЧИКОВ ====================

# class TravelBuddiesView(LoginRequiredMixin, ListView):
#     """Главная страница поиска попутчиков"""
#     template_name = 'events/travel_buddies/travel_buddies.html'
#     context_object_name = 'active_requests'

#     def get_queryset(self):
#         return BuddyRequest.objects.filter(
#             is_active=True,
#             event__date__gte=timezone.now()
#         ).select_related('user', 'event').order_by('-created_at')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # Активные группы пользователя
#         context['my_groups'] = TravelBuddyGroup.objects.filter(
#             members__user=self.request.user,
#             is_active=True
#         ).select_related('event')
        
#         # Рекомендуемые мероприятия для поиска попутчиков
#         user_registrations = Registration.objects.filter(
#             user=self.request.user
#         ).values_list('event_id', flat=True)
        
#         context['recommended_events'] = Event.objects.filter(
#             id__in=user_registrations,
#             date__gte=timezone.now()
#         )[:5]
        
#         return context

# class CreateBuddyRequestView(LoginRequiredMixin, CreateView):
#     """Создание запроса на поиск попутчика"""
#     model = BuddyRequest  # ← Исправьте на модель, а не строку
#     form_class = BuddyRequestForm
#     template_name = 'events/create_buddy_request.html'

#     def form_valid(self, form):
#         event_id = self.kwargs.get('event_id')
#         event = get_object_or_404(Event, id=event_id)
        
#         # Проверяем, зарегистрирован ли пользователь на мероприятие
#         if not Registration.objects.filter(user=self.request.user, event=event).exists():
#             messages.error(self.request, _('Вы должны быть зарегистрированы на мероприятие чтобы искать попутчиков'))
#             return redirect('event_detail', pk=event_id)
        
#         form.instance.event = event
#         form.instance.user = self.request.user
#         messages.success(self.request, _('Запрос на поиск попутчика создан!'))
#         return super().form_valid(form)

#     def get_success_url(self):
#         return reverse_lazy('travel_buddies')

# class CreateBuddyGroupView(LoginRequiredMixin, CreateView):
#     """Создание группы попутчиков"""
#     model = TravelBuddyGroup
#     fields = ['name', 'description', 'max_members']
#     template_name = 'events/travel_buddies/create_group.html'

#     def form_valid(self, form):
#         event_id = self.kwargs.get('event_id')
#         event = get_object_or_404(Event, id=event_id)
        
#         # Проверяем, зарегистрирован ли пользователь на мероприятие
#         if not Registration.objects.filter(user=self.request.user, event=event).exists():
#             messages.error(self.request, _('Вы должны быть зарегистрированы на мероприятие чтобы создавать группу'))
#             return redirect('event_detail', pk=event_id)
        
#         form.instance.event = event
#         form.instance.creator = self.request.user
        
#         response = super().form_valid(form)
        
#         # Автоматически добавляем создателя в группу
#         TravelBuddyMembership.objects.create(
#             group=self.object,
#             user=self.request.user,
#             is_approved=True
#         )
        
#         # Создаем системное сообщение
#         TravelBuddyMessage.objects.create(
#             group=self.object,
#             user=self.request.user,
#             message=_('Группа создана'),
#             is_system_message=True
#         )
        
#         messages.success(self.request, _('Группа попутчиков создана!'))
#         return response

#     def get_success_url(self):
#         return reverse_lazy('group_chat', kwargs={'group_id': self.object.id})

# class GroupChatView(LoginRequiredMixin, DetailView):
#     """Чат группы попутчиков"""
#     model = TravelBuddyGroup
#     template_name = 'events/travel_buddies/group_chat.html'
#     context_object_name = 'group'
#     pk_url_kwarg = 'group_id'

#     def get_queryset(self):
#         return TravelBuddyGroup.objects.select_related('event', 'creator').prefetch_related('members__user')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         group = self.get_object()
        
#         # Проверяем, является ли пользователь участником группы
#         context['is_member'] = TravelBuddyMembership.objects.filter(
#             group=group, user=self.request.user, is_approved=True
#         ).exists()
        
#         context['messages'] = group.messages.select_related('user')[:100]
#         context['members'] = group.members.filter(is_approved=True).select_related('user')
        
#         return context

#     def post(self, request, *args, **kwargs):
#         group = self.get_object()
#         message_text = request.POST.get('message', '').strip()
        
#         # Проверяем, что пользователь является участником группы
#         if not TravelBuddyMembership.objects.filter(group=group, user=request.user, is_approved=True).exists():
#             messages.error(request, _('Вы не являетесь участником этой группы'))
#             return redirect('group_chat', group_id=group.id)
        
#         if message_text:
#             TravelBuddyMessage.objects.create(
#                 group=group,
#                 user=request.user,
#                 message=message_text
#             )
        
#         return redirect('group_chat', group_id=group.id)

# @require_POST
# @login_required
# def join_group(request, group_id):
#     """Вступление в группу попутчиков"""
#     group = get_object_or_404(TravelBuddyGroup, id=group_id, is_active=True)
    
#     # Проверяем, зарегистрирован ли пользователь на мероприятие
#     if not Registration.objects.filter(user=request.user, event=group.event).exists():
#         messages.error(request, _('Вы должны быть зарегистрированы на мероприятие чтобы вступить в группу'))
#         return redirect('event_detail', pk=group.event.id)
    
#     # Проверяем, не является ли пользователь уже участником
#     if TravelBuddyMembership.objects.filter(group=group, user=request.user).exists():
#         messages.info(request, _('Вы уже являетесь участником этой группы'))
#         return redirect('group_chat', group_id=group.id)
    
#     # Проверяем, есть ли свободные места
#     if group.is_full():
#         messages.error(request, _('В группе нет свободных мест'))
#         return redirect('event_detail', pk=group.event.id)
    
#     # Вступаем в группу
#     TravelBuddyMembership.objects.create(
#         group=group,
#         user=request.user,
#         is_approved=True
#     )
    
#     # Создаем системное сообщение
#     TravelBuddyMessage.objects.create(
#         group=group,
#         user=request.user,
#         message=_('присоединился к группе'),
#         is_system_message=True
#     )
    
#     messages.success(request, _('Вы успешно вступили в группу!'))
#     return redirect('group_chat', group_id=group.id)

# @require_POST
# @login_required
# def leave_group(request, group_id):
#     """Выход из группы попутчиков"""
#     group = get_object_or_404(TravelBuddyGroup, id=group_id)
#     membership = get_object_or_404(TravelBuddyMembership, group=group, user=request.user)
    
#     membership.delete()
    
#     # Создаем системное сообщение
#     TravelBuddyMessage.objects.create(
#         group=group,
#         user=request.user,
#         message=_('покинул группу'),
#         is_system_message=True
#     )
    
#     messages.success(request, _('Вы вышли из группы'))
#     return redirect('event_detail', pk=group.event.id)

# @login_required
# def my_buddy_requests(request):
#     """Мои запросы на поиск попутчиков"""
#     buddy_requests = BuddyRequest.objects.filter(
#         user=request.user
#     ).select_related('event').order_by('-created_at')
    
#     return render(request, 'events/travel_buddies/my_requests.html', {
#         'buddy_requests': buddy_requests
#     })

# @require_POST
# @login_required
# def delete_buddy_request(request, request_id):
#     """Удаление запроса на поиск попутчика"""
#     buddy_request = get_object_or_404(BuddyRequest, id=request_id, user=request.user)
#     buddy_request.delete()
    
#     messages.success(request, _('Запрос удален'))
#     return redirect('my_buddy_requests')
# # ============================================================

class ArchiveEventsView(ListView):
    """Архив прошедших мероприятий"""
    template_name = 'events/archive.html'
    paginate_by = 20
    context_object_name = 'events'
    
    def get_queryset(self):
        # Архив внутренних мероприятий
        internal_archive = Event.objects.filter(
            Q(is_active=False) | Q(date__lt=timezone.now())
        )
        
        # Архив внешних мероприятий
        external_archive = ExternalEvent.objects.filter(
            is_archived=True
        )
        
        combined = []
        
        for event in internal_archive:
            combined.append({
                'type': 'internal',
                'object': event,
                'title': event.title,
                'date': event.date,
                'location': event.location,
                'is_past': event.date < timezone.now(),
                'source_name': 'EventHub',
            })
        
        for event in external_archive:
            combined.append({
                'type': 'external', 
                'object': event,
                'title': event.title,
                'date': event.date,
                'location': event.location,
                'is_past': True,
                'source_name': event.source.name,
            })

        # Сортируем по дате (сначала самые новые прошедшие)        
        combined.sort(key=lambda x: x['date'], reverse=True)
        return combined
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Архив мероприятий'
        return context
    

class ExternalEventsView(ListView):
    """Только внешние мероприятия"""
    template_name = 'events/external_events.html'
    paginate_by = 20
    context_object_name = 'events'
    
    def get_queryset(self):
        return ExternalEvent.objects.filter(
            is_archived=False,
            date__gte=timezone.now()
        ).select_related('source').order_by('date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Мероприятия с других платформ'
        context['sources'] = ExternalEventSource.objects.filter(is_active=True)
        return context
    

def get_ai_recommended_events(request):
    """Представление для AI-рекомендаций"""
    if request.user.is_authenticated:
        engine = AIRecommendationEngine()
        recommendations = engine.get_hybrid_recommendations(request.user, 6)
    else:
        # Для неавторизованных - популярные мероприятия
        from .models import Event
        recommendations = Event.objects.filter(is_active=True).annotate(
            registrations_count=Count('registrations')
        ).order_by('-registrations_count')[:6]
    
    return recommendations

class EventsMapView(TemplateView):
    template_name = "events/events_map.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем активные мероприятия с координатами
        events = Event.objects.filter(
            Q(latitude__isnull=False) & 
            Q(longitude__isnull=False) &
            Q(status='active')  # или ваше условие для активных мероприятий
        ).select_related('category')
        
        context['events'] = events
        return context

class OrganizerSolutionsView(TemplateView):
    template_name = "events/organizer_solutions.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solutions'] = [
            {
                'title': _('Продвижение мероприятий'),
                'description': _('Расширенная видимость в поиске, email-рассылки, таргетированная реклама'),
                'icon': 'fas fa-bullhorn',
                'features': [
                    _('SEO оптимизация мероприятий'),
                    _('Email маркетинг'),
                    _('Таргетированная реклама'),
                    _('Социальные сети интеграция')
                ]
            },
            {
                'title': _('Система продажи билетов'),
                'description': _('Простая интеграция, мгновенные подтверждения, мобильные билеты'),
                'icon': 'fas fa-ticket-alt',
                'features': [
                    _('Онлайн продажа билетов'),
                    _('Мгновенные подтверждения'),
                    _('Мобильные билеты'),
                    _('Система скидок и промокодов')
                ]
            },
            {
                'title': _('Аналитика и отчетность'),
                'description': _('Детальная статистика, отслеживание конверсий, ROI-аналитика'),
                'icon': 'fas fa-chart-bar',
                'features': [
                    _('Детальная аналитика'),
                    _('Отслеживание конверсий'),
                    _('ROI аналитика'),
                    _('Кастомные отчеты')
                ]
            },
            {
                'title': _('Управление участниками'),
                'description': _('Регистрация, проверка, коммуникация и управление участниками'),
                'icon': 'fas fa-users',
                'features': [
                    _('Онлайн регистрация'),
                    _('QR-код проверка'),
                    _('Массовая рассылка'),
                    _('Сегментация участников')
                ]
            },
            {
                'title': _('Мобильное приложение'),
                'description': _('Собственное мобильное приложение для вашего мероприятия'),
                'icon': 'fas fa-mobile-alt',
                'features': [
                    _('Кастомное мобильное приложение'),
                    _('Push уведомления'),
                    _('Интерактивная программа'),
                    _('Карта мероприятия')
                ]
            },
            {
                'title': _('Интеграции и API'),
                'description': _('Интеграция с популярными сервисами и кастомные решения'),
                'icon': 'fas fa-plug',
                'features': [
                    _('REST API'),
                    _('Zapier интеграция'),
                    _('Кастомные интеграции'),
                    _('Webhooks поддержка')
                ]
            }
        ]
        return context
    

# ==================== СТРАНИЦЫ ФУТЕРА И СТАТИЧЕСКИЕ СТРАНИЦЫ ====================

class ContactView(TemplateView):
    template_name = 'events/footer/contact.html'
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Отправка email
        try:
            send_mail(
                f'Contact Form: {subject}',
                f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}',
                email,
                ['support@eventhub.ru'],
                fail_silently=False,
            )
            messages.success(request, _('Ваше сообщение отправлено! Мы ответим вам в ближайшее время.'))
        except Exception as e:
            messages.error(request, _('Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.'))
        
        return redirect('contact')

class FAQView(TemplateView):
    template_name = 'events/footer/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faq_categories'] = [
            {
                'title': _('Регистрация и аккаунт'),
                'questions': [
                    {
                        'question': _('Как зарегистрироваться на мероприятие?'),
                        'answer': _('Выберите мероприятие, нажмите "Зарегистрироваться" и следуйте инструкциям. Для платных мероприятий потребуется оплата.')
                    },
                    {
                        'question': _('Как восстановить пароль?'),
                        'answer': _('На странице входа нажмите "Забыли пароль?" и следуйте инструкциям для восстановления.')
                    },
                    {
                        'question': _('Как подтвердить email?'),
                        'answer': _('После регистрации вам на email придет письмо с ссылкой для подтверждения. Перейдите по этой ссылке.')
                    },
                    {
                        'question': _('Можно ли изменить данные профиля?'),
                        'answer': _('Да, в личном кабинете вы можете изменить свои данные, включая имя, email и настройки уведомлений.')
                    }
                ]
            },
            {
                'title': _('Оплата и возвраты'),
                'questions': [
                    {
                        'question': _('Какие способы оплаты принимаются?'),
                        'answer': _('Мы принимаем банковские карты, ЮMoney, и другие популярные платежные системы.')
                    },
                    {
                        'question': _('Как вернуть деньги за билет?'),
                        'answer': _('Возврат возможен за 48 часов до мероприятия. Обратитесь в поддержку с номером заказа.')
                    },
                    {
                        'question': _('Безопасны ли платежи?'),
                        'answer': _('Да, все платежи защищены SSL-шифрованием и обрабатываются через проверенные платежные системы.')
                    }
                ]
            },
            {
                'title': _('Мероприятия и регистрация'),
                'questions': [
                    {
                        'question': _('Как найти подходящее мероприятие?'),
                        'answer': _('Используйте фильтры по категориям, дате, цене и формату. Также доступен поиск по ключевым словам.')
                    },
                    {
                        'question': _('Можно ли отменить регистрацию?'),
                        'answer': _('Да, в личном кабинете в разделе "Мои регистрации" вы можете отменить регистрацию.')
                    },
                    {
                        'question': _('Что делать, если мероприятие отменено?'),
                        'answer': _('При отмене мероприятия все зарегистрированные участники получат уведомление и автоматический возврат средств.')
                    }
                ]
            },
            {
                'title': _('Для организаторов'),
                'questions': [
                    {
                        'question': _('Как создать мероприятие?'),
                        'answer': _('Войдите в аккаунт, нажмите "Создать мероприятие" и заполните все необходимые поля формы.')
                    },
                    {
                        'question': _('Как продвигать мероприятие?'),
                        'answer': _('Используйте наши инструменты продвижения: email-рассылки, SEO-оптимизацию и интеграцию с социальными сетями.')
                    },
                    {
                        'question': _('Какая комиссия за продажу билетов?'),
                        'answer': _('Комиссия зависит от выбранного тарифа. Подробности смотрите в разделе "Тарифы для организаторов".')
                    }
                ]
            }
        ]
        return context

class PrivacyPolicyView(TemplateView):
    template_name = 'events/footer/privacy_policy.html'

class TermsOfUseView(TemplateView):
    template_name = 'events/footer/terms_of_use.html'

class RefundPolicyView(TemplateView):
    template_name = 'events/footer/refund_policy.html'

class OrganizerSolutionsView(TemplateView):
    template_name = 'events/footer/organizer_solutions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solutions'] = [
            {
                'title': _('Продвижение мероприятий'),
                'description': _('Расширенная видимость в поиске, email-рассылки, таргетированная реклама'),
                'icon': '📢',
                'features': [
                    _('SEO оптимизация мероприятий'),
                    _('Email маркетинг'),
                    _('Таргетированная реклама'),
                    _('Социальные сети интеграция')
                ]
            },
            {
                'title': _('Система продажи билетов'),
                'description': _('Простая интеграция, мгновенные подтверждения, мобильные билеты'),
                'icon': '🎫',
                'features': [
                    _('Онлайн продажа билетов'),
                    _('Мгновенные подтверждения'),
                    _('Мобильные билеты'),
                    _('Система скидок и промокодов')
                ]
            },
            {
                'title': _('Аналитика и отчетность'),
                'description': _('Детальная статистика, отслеживание конверсий, ROI-аналитика'),
                'icon': '📊',
                'features': [
                    _('Детальная аналитика'),
                    _('Отслеживание конверсий'),
                    _('ROI аналитика'),
                    _('Кастомные отчеты')
                ]
            },
            {
                'title': _('Управление участниками'),
                'description': _('Регистрация, проверка, коммуникация и управление участниками'),
                'icon': '👥',
                'features': [
                    _('Онлайн регистрация'),
                    _('QR-код проверка'),
                    _('Массовая рассылка'),
                    _('Сегментация участников')
                ]
            },
            {
                'title': _('Мобильное приложение'),
                'description': _('Собственное мобильное приложение для вашего мероприятия'),
                'icon': '📱',
                'features': [
                    _('Кастомное мобильное приложение'),
                    _('Push уведомления'),
                    _('Интерактивная программа'),
                    _('Карта мероприятия')
                ]
            },
            {
                'title': _('Интеграции и API'),
                'description': _('Интеграция с популярными сервисами и кастомные решения'),
                'icon': '🔌',
                'features': [
                    _('REST API'),
                    _('Zapier интеграция'),
                    _('Кастомные интеграции'),
                    _('Webhooks поддержка')
                ]
            }
        ]
        return context

class OrganizerGuidelinesView(TemplateView):
    template_name = 'events/footer/organizer_guidelines.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['guidelines'] = [
            {
                'title': _('Требования к мероприятиям'),
                'items': [
                    _('Мероприятие должно соответствовать законодательству РФ'),
                    _('Запрещена пропаганда насилия и дискриминации'),
                    _('Необходимо предоставить точную информацию о мероприятии'),
                    _('Обязательно указание реальной цены и условий участия')
                ]
            },
            {
                'title': _('Рекомендации по оформлению'),
                'items': [
                    _('Используйте качественные изображения'),
                    _('Подробно опишите программу мероприятия'),
                    _('Укажите точное время и место проведения'),
                    _('Добавьте информацию о спикерах/организаторах')
                ]
            },
            {
                'title': _('Правила взаимодействия с участниками'),
                'items': [
                    _('Своевременно отвечайте на вопросы'),
                    _('Уведомляйте об изменениях в программе'),
                    _('Соблюдайте условия возврата средств'),
                    _('Предоставляйте необходимую информацию')
                ]
            }
        ]
        return context

class OrganizerResourcesView(TemplateView):
    template_name = 'events/footer/organizer_resources.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resources'] = [
            {
                'title': _('Шаблоны мероприятий'),
                'description': _('Готовые шаблоны для разных типов мероприятий'),
                'type': 'template'
            },
            {
                'title': _('Гайды по продвижению'),
                'description': _('Пошаговые инструкции по привлечению аудитории'),
                'type': 'guide'
            },
            {
                'title': _('Маркетинговые материалы'),
                'description': _('Баннеры, пресс-релизы и другие материалы'),
                'type': 'marketing'
            },
            {
                'title': _('Аналитические отчеты'),
                'description': _('Примеры отчетов и дашбордов'),
                'type': 'analytics'
            }
        ]
        return context

class PricingView(TemplateView):
    template_name = 'events/footer/pricing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = [
            {
                'name': _('Базовый'),
                'price': '0₽',
                'period': _('бесплатно'),
                'description': _('Идеально для небольших мероприятий'),
                'features': [
                    _('До 3 мероприятий одновременно'),
                    _('Базовая аналитика'),
                    _('Email поддержка'),
                    _('Стандартные шаблоны'),
                    _('До 100 участников на мероприятие')
                ],
                'button_text': _('Начать бесплатно'),
                'popular': False
            },
            {
                'name': _('Профессиональный'),
                'price': '2990₽',
                'period': _('/месяц'),
                'description': _('Для растущего бизнеса'),
                'features': [
                    _('Неограниченное количество мероприятий'),
                    _('Расширенная аналитика'),
                    _('Приоритетная поддержка'),
                    _('Кастомные шаблоны'),
                    _('Продвижение в поиске'),
                    _('До 1000 участников на мероприятие'),
                    _('Интеграция с CRM')
                ],
                'button_text': _('Выбрать план'),
                'popular': True
            },
            {
                'name': _('Премиум'),
                'price': '7990₽',
                'period': _('/месяц'),
                'description': _('Для крупных мероприятий'),
                'features': [
                    _('Все функции Профессионального плана'),
                    _('Персональный менеджер'),
                    _('White-label решение'),
                    _('API доступ'),
                    _('Расширенные интеграции'),
                    _('Неограниченное количество участников'),
                    _('Кастомная разработка')
                ],
                'button_text': _('Связаться с нами'),
                'popular': False
            }
        ]
        return context

class SuccessStoriesView(TemplateView):
    template_name = 'events/footer/success_stories.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stories'] = [
            {
                'title': _('Музыкальный фестиваль "Волна"'),
                'description': _('Организовали фестиваль на 5000+ участников с помощью наших инструментов'),
                'results': [
                    _('+150% к продажам билетов'),
                    _('Увеличили охват аудитории в 3 раза'),
                    _('Снизили затраты на организацию на 40%')
                ],
                'image': '/static/images/success/story1.jpg'
            },
            {
                'title': _('Бизнес-конференция "Future Tech"'),
                'description': _('Крупнейшая IT-конференция региона использовала нашу платформу'),
                'results': [
                    _('2000+ участников'),
                    _('Автоматизировали все процессы'),
                    _('Получили детальную аналитику')
                ],
                'image': '/static/images/success/story2.jpg'
            }
        ]
        return context

class AboutView(TemplateView):
    template_name = 'events/footer/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = [
            {
                'name': 'Алексей Петров', 
                'role': _('Основатель & CEO'), 
                'bio': _('15+ лет в event-индустрии, эксперт по организации крупных мероприятий'),
                'image': '/static/images/team/alexey.jpg'
            },
            {
                'name': 'Мария Иванова', 
                'role': _('CTO'), 
                'bio': _('Эксперт в разработке масштабируемых систем, 10+ лет в IT'),
                'image': '/static/images/team/maria.jpg'
            },
            {
                'name': 'Дмитрий Сидоров', 
                'role': _('Head of Marketing'), 
                'bio': _('Специалист по digital-маркетингу и продвижению мероприятий'),
                'image': '/static/images/team/dmitry.jpg'
            }
        ]
        context['stats'] = {
            'events_organized': '10,000+',
            'happy_users': '500,000+',
            'cities': '50+',
            'countries': '5+'
        }
        return context

class BlogView(TemplateView):
    template_name = 'events/footer/blog.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts'] = [
            {
                'title': _('Как организовать успешное мероприятие в 2024'),
                'excerpt': _('Советы и инструменты для организаторов мероприятий'),
                'date': '15 января 2024',
                'author': 'Мария Иванова',
                'category': _('Организация')
            },
            {
                'title': _('Тренды в event-индустрии'),
                'excerpt': _('Новые технологии и подходы к проведению мероприятий'),
                'date': '10 января 2024',
                'author': 'Алексей Петров',
                'category': _('Тренды')
            }
        ]
        return context

class CareersView(TemplateView):
    template_name = 'events/footer/careers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['open_positions'] = [
            {
                'title': _('Frontend разработчик'),
                'department': _('Технологии'),
                'location': _('Москва / Удаленно'),
                'type': _('Полная занятость')
            },
            {
                'title': _('Менеджер по работе с клиентами'),
                'department': _('Продажи'),
                'location': _('Москва'),
                'type': _('Полная занятость')
            }
        ]
        return context

class PressView(TemplateView):
    template_name = 'events/footer/press.html'

class PartnersView(TemplateView):
    template_name = 'events/footer/partners.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partners'] = [
            {
                'name': 'EventTech',
                'description': _('Технологический партнер'),
                'logo': '/static/images/partners/eventtech.png'
            },
            {
                'name': 'MeetupPro',
                'description': _('Партнер по организации мероприятий'),
                'logo': '/static/images/partners/meetupro.png'
            }
        ]
        return context

class APIDocsView(TemplateView):
    template_name = 'events/pages/api_docs.html'

class SitemapView(TemplateView):
    template_name = 'events/pages/sitemap.html'

class GameProfileView(LoginRequiredMixin, View):
    """
    Представление для игрового профиля пользователя
    """
    def get(self, request):
        try:
            # Заглушка для игрового профиля
            game_profile_data = {
                'user_id': request.user.id,
                'username': request.user.username,
                'game_stats': {
                    'total_events_attended': 5,
                    'total_points': 150,
                    'current_level': 1,
                    'favorite_category': 'Музыка',
                    'member_since': '2024-01-01'
                },
                'achievements': [
                    {'name': 'Первый шаг', 'completed': True},
                    {'name': 'Постоянный посетитель', 'completed': True},
                    {'name': 'Социальная бабочка', 'completed': False},
                    {'name': 'Исследователь', 'completed': True}
                ],
                'recent_activity': [
                    {'event': 'Концерт рок-группы', 'date': '2024-01-15', 'points': 50},
                    {'event': 'Выставка искусств', 'date': '2024-01-10', 'points': 30},
                    {'event': 'Кинофестиваль', 'date': '2024-01-05', 'points': 70}
                ]
            }
            
            return JsonResponse({
                'success': True,
                'profile': game_profile_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class LeaderboardView(LoginRequiredMixin, TemplateView):
    """
    Представление для страницы таблицы лидеров
    """
    template_name = 'events/leaderboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Заглушка для данных таблицы лидеров
        leaderboard_data = [
            {
                'rank': 1,
                'username': 'Лидер',
                'points': 1000,
                'level': 5,
                'avatar': '/static/images/avatars/1.png'
            },
            {
                'rank': 2,
                'username': 'Второй',
                'points': 800,
                'level': 4,
                'avatar': '/static/images/avatars/2.png'
            },
            {
                'rank': 3,
                'username': 'Третий',
                'points': 600,
                'level': 3,
                'avatar': '/static/images/avatars/3.png'
            },
            {
                'rank': 4,
                'username': self.request.user.username,
                'points': 150,
                'level': 1,
                'avatar': '/static/images/avatars/default.png'
            }
        ]
        
        context['leaderboard'] = leaderboard_data
        context['user_rank'] = 4  # Ранг текущего пользователя
        context['total_players'] = len(leaderboard_data)
        
        return context
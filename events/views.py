from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg
from django_filters import FilterSet, CharFilter, NumberFilter, ChoiceFilter, DateFilter
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Event, Category, Registration, Advertisement, Favorite, Review
from .forms import EventForm, RegistrationForm, ReviewForm


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
    paginate_by = 9

    def get_queryset(self):
        queryset = Event.objects.filter(
            is_active=True, 
            date__gte=timezone.now()
        ).select_related('category', 'organizer').annotate(
            registrations_count=Count('registrations'),
            avg_rating=Avg('reviews__rating')
        )
        
        # Фильтрация по категории
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
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
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'date')
        
        # ДОБАВЛЯЕМ ИНФОРМАЦИЮ О РЕГИСТРАЦИЯХ И ИЗБРАННОМ
        if self.request.user.is_authenticated:
            # ID мероприятий на которые пользователь зарегистрирован
            user_events = Registration.objects.filter(
                user=self.request.user
            ).values_list('event_id', flat=True)
            context['user_registered_events'] = user_events
            
            # Помечаем избранные события
            for event in context['events']:
                event.is_favorite = Favorite.objects.filter(
                    user=self.request.user, 
                    event=event
                ).exists()
        
        return context


class EventDetailView(DetailView):
    """Детальная страница мероприятия"""
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_queryset(self):
        return Event.objects.select_related(
            'category', 'organizer'
        ).prefetch_related(
            'reviews', 'reviews__user'
        ).annotate(
            registrations_count=Count('registrations'),
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        
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
        
        context['available_seats'] = event.capacity - event.registrations_count
        context['reviews'] = event.reviews.all().select_related('user')
        context['review_form'] = ReviewForm()
        
        return context


class EventCreateView(LoginRequiredMixin, CreateView):
    """Создание мероприятия"""
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('event_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, 'Мероприятие успешно создано!')
        return super().form_valid(form)


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
        ).select_related('category', 'organizer').annotate(
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
        ).select_related('category')
        return context


class FavoriteListView(LoginRequiredMixin, ListView):
    """Страница с избранными мероприятиями пользователя"""
    model = Favorite
    template_name = 'events/favorite_list.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('event', 'event__category').annotate(
            registrations_count=Count('event__registration'),
            average_rating=Avg('event__reviews__rating')
        )


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
    registrations = Registration.objects.filter(
        user=request.user
    ).select_related('event', 'event__category').order_by('-registration_date')
    
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
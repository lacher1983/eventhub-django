from django.http import JsonResponse, HttpResponseServerError
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Prefetch, Q, Count, Avg
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django_filters import FilterSet, CharFilter, NumberFilter, ChoiceFilter, DateFilter
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import VideoAd
from .models import Event, Category, Registration, Advertisement, Favorite, Review, Cart, CartItem, Order, OrderItem
from .forms import EventForm, RegistrationForm, ReviewForm, AddToCartForm, CheckoutForm, PaymentForm
from .utils.notifications import send_registration_confirmation
from .filters import EventFilter
from django.views.decorators.cache import cache_page
import logging

@cache_page(60 * 15)  # Кэшировать на 15 минут
def event_list(request):
    pass

def organizer_required(user):
    return user.is_authenticated and user.role == 'organizer'

class OrganizerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return organizer_required(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, "Требуются права организатора для создания мероприятий")
        return redirect('events:event_list')

# Использовать в CBV
class EventCreateView(OrganizerRequiredMixin, CreateView):
    pass

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
    """Обработка показа рекламы (импрессии)"""
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
        ).select_related('category', 'organizer'
        ).prefetch_related('reviews'
        ).annotate(
            registrations_count=Count('registrations'),
            avg_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews')
        )

        # Применяем фильтры
        self.filterset = EventFilter(self.request.GET, queryset=queryset)
        queryset = self.filterset.qs

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

        # если пользователь авторизован
        if self.request.user.is_authenticated:
            queryset = queryset.prefetch_related(
                Prefetch('favorited_by', 
                        queryset=Favorite.objects.filter(user=self.request.user),
                        to_attr='user_favorites')
            )

        return queryset
        
        
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
            registrations_count=Count('event__registrations'),
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
    
    return redirect('events:event_detail', pk=pk)


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
        return redirect('events:event_detail', pk=event_id)
    
    # Проверяем, не оставлял ли уже отзыв
    existing_review = Review.objects.filter(user=request.user, event=event).first()
    if existing_review:
        messages.info(request, 'Вы уже оставляли отзыв на это мероприятие')
        return redirect('events:event_detail', pk=event_id)
    
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
            return redirect('events:event_detail', pk=review.event.id)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'events/edit_review.html', {
        'form': form,
        'review': review
    })

def my_view(request):
    # Пробуем получить активное видео
    try:
        video_ad = VideoAd.objects.get(is_active=True)
    except VideoAd.DoesNotExist:
        video_ad = None  # Если ничего не найдено, передаем None

    context = {
        'video_ad': video_ad, 
    }
    return render(request, 'my_template.html', context)


def get_user_cart(user):
    """Вспомогательная функция для получения корзины пользователя"""
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

@login_required
def add_to_cart(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Отладочная информация
    print(f"Event ID: {event.id}")
    print(f"Title: {event.title}")
    print(f"Price: {event.price}")
    print(f"Is Free: {event.is_free}")
    print(f"Tickets Available: {event.tickets_available}")
    
    # Проверяем, платное ли мероприятие
    if not event.is_free and event.price <= 0:
        messages.error(request, "Это мероприятие бесплатное. Регистрация не требуется.")
        return redirect('events:event_detail', pk=event_id)
    
    # Проверка наличия билетов (новая проверка)
    if event.tickets_available <= 0:
        messages.error(request, "Извините, билеты закончились.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Извините, билеты закончились."
            }, status=400)
        return redirect('events:event_detail', pk=event_id)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']

            # Дополнительная проверка количества
            if quantity > event.tickets_available:
                messages.error(request, f"Доступно только {event.tickets_available} билетов.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f"Доступно только {event.tickets_available} билетов."
                    }, status=400)
                return redirect('events:event_detail', pk=event_id)
            
            # Фиксируем цену при добавлении (исправление)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                event=event,
                defaults={
                    'quantity': quantity,
                    'price': event.price  # Фиксируем цену
                }
            )

            if not created:
                # Проверяем, не превысит ли общее количество доступное
                if cart_item.quantity + quantity > event.tickets_available:
                    messages.error(request, f"Нельзя добавить больше {event.tickets_available} билетов.")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': f"Нельзя добавить больше {event.tickets_available} билетов."
                        }, status=400)
                    return redirect('events:event_detail', pk=event_id)
                
                cart_item.quantity += quantity
                cart_item.save()
            
            messages.success(request, f"Добавлено в корзину: {event.title}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'cart_count': cart.items_count,
                    'message': f"Добавлено в корзину: {event.title}"
                })
            
            return redirect('events:event_detail', pk=event_id)
        else:
            # Обработка невалидной формы для AJAX (добавил новый код)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.as_json()
                }, status=400)
            messages.error(request, "Произошла ошибка.")
            return redirect('events:event_detail', pk=event_id)
    
    return redirect('events:event_detail', pk=event_id)

@login_required
def cart_view(request):
    # Оптимизация запросов с prefetch_related
    try:
        cart = Cart.objects.prefetch_related('items__event').get(user=request.user)
    except Cart.DoesNotExist:
        # Если корзины нет, создаем новую
        cart = Cart.objects.create(user=request.user)

    return render(request, 'events/cart.html', {'cart': cart})


@login_required
@require_POST
def update_cart_item(request, item_id):
    print(f"UPDATE request: {request.POST}")

    try:
        # Ищем корзину пользователя и товар именно в этой корзине
        cart = get_user_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        # Для AJAX-запросов
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            action = request.POST.get('action')
            print(f"AJAX Action: {action}")

            if action == 'increase':
                # Проверка максимального количества
                if cart_item.quantity >= cart_item.event.tickets_available:
                    return JsonResponse({
                        'success': False,
                        'message': f'Нельзя добавить больше {cart_item.event.tickets_available} билетов'
                    })
                else:
                    cart_item.quantity += 1
                    cart_item.save()

            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    # Если количество становится 0, удаляем товар
                    event_title = cart_item.event.title
                    cart_item.delete()
                    return JsonResponse({
                        'success': True,
                        'removed': True,
                        'message': f'Товар "{event_title}" удален из корзины',
                        'cart_total': cart.total_price,
                        'cart_count': cart.items_count
                    })
        
            elif action == 'remove':
                event_title = cart_item.event.title
                cart_item.delete()
                return JsonResponse({
                    'success': True,
                    'removed': True,
                    'message': f'Товар "{event_title}" удален из корзины',
                    'cart_total': cart.total_price,
                    'cart_count': cart.items_count
                })

            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Неверное действие'
                })

            # Возвращаем успешный ответ для AJAX
            return JsonResponse({
                'success': True,
                'quantity': cart_item.quantity,
                'item_total': cart_item.total_price,
                'cart_total': cart.total_price,
                'cart_count': cart.items_count,
                'removed': False
            })

        else:
            # Для обычных POST-запросов (если JavaScript отключен)
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity > 0:
                if quantity <= cart_item.event.tickets_available:
                    cart_item.quantity = quantity
                    cart_item.save()
                    messages.success(request, "Количество обновлено")
                else:
                    messages.error(request, f"Нельзя добавить больше {cart_item.event.tickets_available} билетов")
            else:
                cart_item.delete()
                messages.success(request, "Товар удален из корзины")
            
            return redirect('events:cart')

    except CartItem.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Товар не найден'})
        messages.error(request, "Товар не найден")
        return redirect('events:cart')
    
    except Exception as e:
        print(f"Error in update_cart_item: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, "Произошла ошибка при обновлении корзины")
        return redirect('events:cart')
    
@login_required
@require_POST
def remove_from_cart(request, item_id):
    print(f"REMOVE request: {request.POST}")
    """Удаление товара из корзины"""
    cart = get_user_cart(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    event_title = cart_item.event.title
    cart_item.delete()
    
    messages.success(request, f"Товар '{event_title}' удален из корзины")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Товар '{event_title}' удален из корзины",
            'cart_total': cart.total_price,
            'cart_count': cart.items_count
        })
    
    return redirect('events:cart')

@login_required
def cart_detail(request):
    """Альтернативное имя для cart_view"""
    return cart_view(request)

@login_required
def checkout(request):
    cart = get_user_cart(request.user)
    
    if cart.items_count == 0:
        messages.warning(request, "Ваша корзина пуста")
        return redirect('event_list')
    
    # Проверка наличия всех билетов перед оформлением
    for item in cart.items.all():
        if item.quantity > item.event.tickets_available:
            messages.error(request, 
                f"Для мероприятия '{item.event.title}' доступно только {item.event.tickets_available} билетов.")
            return redirect('cart_view')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_amount = cart.total_price
            order.save()
            
            # Создаем элементы заказа
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    event=cart_item.event,
                    quantity=cart_item.quantity,
                    price=cart_item.price # Используем цену из корзины, а не из event
                )
            
            request.session['order_id'] = order.id
            return redirect('events:payment')
    else:
        # Предзаполняем форму данными пользователя
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = CheckoutForm(initial=initial_data)
    
    return render(request, 'events/checkout.html', {
        'cart': cart,
        'form': form
    })

@login_required
def payment(request):
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, "Заказ не найден")
        return redirect('events:cart')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status == 'paid':
        messages.info(request, "Этот заказ уже оплачен")
        return redirect('events:order_success', order_id=order.id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Здесь будет интеграция с платежной системой
            # Для демонстрации просто помечаем как оплаченное
            order.status = 'paid'
            order.payment_method = form.cleaned_data['payment_method']
            order.payment_date = timezone.now()
            order.save()
            
            # Обновляем количество доступных билетов
            for order_item in order.items.all():
                event = order_item.event
                event.tickets_available -= order_item.quantity
                event.save()

            # Очищаем корзину
            cart = get_user_cart(request.user)
            cart.items.all().delete()

            # Очищаем сессию
            if 'order_id' in request.session:
                del request.session['order_id']
            
            # Отправляем email
            send_order_confirmation(order)
            
            messages.success(request, "Оплата прошла успешно! Чек отправлен на email.")
            return redirect('events:order_success', order_id=order.id)
    else:
        form = PaymentForm()
    
    return render(request, 'events/payment.html', {
        'order': order,
        'form': form
    })

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'events/order_success.html', {'order': order})

def send_order_confirmation(order):
    subject = f"Подтверждение заказа #{order.order_number}"
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'user': order.user
    })
    plain_message = f"Спасибо за заказ #{order.order_number}. Сумма: {order.total_amount} руб."
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message,
        fail_silently=False
    )

@login_required
def debug_cart(request):
    """Отладочная страница для проверки корзины"""
    cart = get_user_cart(request.user)

    # Отладочная информация
    print(f"DEBUG: User {request.user.username}")
    print(f"DEBUG: Cart ID {cart.id}")
    print(f"DEBUG: Cart items {cart.items.count()}")

    context = {
        'cart': cart,
        'cart_items': cart.items.all().select_related('event'),
        'cart_total': cart.total_price,
        'cart_count': cart.items_count,
        'all_cart_items': CartItem.objects.filter(cart=cart),
    }
    
    return render(request, 'events/debug_cart.html', context)
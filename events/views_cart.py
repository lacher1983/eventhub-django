from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
import stripe
from .models import Cart, CartItem, Order, OrderItem, Event
from .forms import AddToCartForm, CheckoutForm, PaymentForm

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
        return redirect('event_detail', pk=event_id)
    
    # Проверка наличия билетов (новая проверка)
    if event.tickets_available <= 0:
        messages.error(request, "Извините, билеты закончились.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Извините, билеты закончились."
            }, status=400)
        return redirect('event_detail', pk=event_id)
    
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
                return redirect('event_detail', pk=event_id)
            
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
                    return redirect('event_detail', pk=event_id)
                

                cart_item.quantity += quantity
                cart_item.save()
            
            messages.success(request, f"Добавлено в корзину: {event.title}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'cart_count': cart.items_count,
                    'message': f"Добавлено в корзину: {event.title}"
                })
            
            return redirect('event_detail', pk=event_id)
        else:
            # Обработка невалидной формы для AJAX (добавил новый код)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.as_json()
                }, status=400)
            messages.error(request, "Произошла ошибка.")
            return redirect('event_detail', pk=event_id)
    
    return redirect('event_detail', pk=event_id)

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
def update_cart_item(request, item_id):
    # Ищем корзину пользователя и товар именно в этой корзине (мы же за безопасность)
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart) # Важно: ищем в конкретной корзине, чтобы не грабанули

    if request.method == 'POST':
        action = request.POST.get('action')

        # Проверка доступности билетов
        available_tickets = cart_item.event.tickets_available
        
        if action == 'increase':
            # Проверка максимального количества
            if cart_item.quantity >= available_tickets:
                messages.error(request, f"Нельзя добавить больше {available_tickets} билетов.")
            else:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, "Количество обновлено")

        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                messages.success(request, "Количество обновлено")
            else:
                messages.warning(request, "Количество не может быть меньше 1")

        elif action == 'remove':
            event_title = cart_item.event.title
            cart_item.delete()
            messages.success(request, f"Товар '{event_title}' удален из корзины")

        else:
            messages.error(request, "Неверное действие")

    return redirect('cart_view')
        
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
            return redirect('payment')
    else:
        form = CheckoutForm()
    
    return render(request, 'events/checkout.html', {
        'cart': cart,
        'form': form
    })

@login_required
def payment(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('cart_view')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Здесь будет интеграция с платежной системой
            # Для демонстрации просто помечаем как оплаченное
            order.status = 'paid'
            order.payment_date = timezone.now()
            order.save()
            
            # Обновляем количество доступных билетов
            for order_item in order.items.all():
                event = order_item.event
                event.tickets_available -= order_item.quantity
                event.save()

            # Очищаем корзину
            CartItem.objects.filter(cart__user=request.user).delete()

            # Очищаем сессию (исправление)
            del request.session['order_id']
            
            # Отправляем email
            send_order_confirmation(order)
            
            messages.success(request, "Оплата прошла успешно! Чек отправлен на email.")
            return redirect('order_success', order_id=order.id)
    else:
        form = PaymentForm()
    
    return render(request, 'events/payment.html', {
        'order': order,
        'form': form,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
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
        html_message=html_message
    )
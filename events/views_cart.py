from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import stripe
from .models import Cart, CartItem, Order, OrderItem, Event
from .forms import AddToCartForm, CheckoutForm, PaymentForm
import json


@login_required
def cart_detail(request):
    """Детальная страница корзины"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        total_amount = sum(item.total_price for item in cart_items)
        total_quantity = sum(item.quantity for item in cart_items)

    except Cart.DoesNotExist:  # Правильное имя исключения
        cart = None
        cart_items = []
        total_quantity = 0
        total_amount = 0

    except Exception as e:
        messages.error(request, f'Ошибка при загрузке корзины: {str(e)}')
        cart = None
        cart_items = []
        total_quantity = 0
        total_amount = 0

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_amount': total_amount,
        'total_quantity': total_quantity,
    }
    return render(request, 'events/cart_detail.html', context)
        
    # except Exception as e:
    #     messages.error(request, f'Ошибка при загрузке корзины: {str(e)}')
    #     return redirect('event_list')
    
@login_required
@require_POST
def cart_add(request, event_id):
    """Добавление мероприятия в корзину"""
    try:
        event = get_object_or_404(Event, id=event_id, is_active=True)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Проверяем, не добавлено ли уже мероприятие в корзину
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            event=event,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        messages.success(request, f'Мероприятие "{event.title}" добавлено в корзину')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Мероприятие добавлено в корзину',
                'cart_count': cart.items.count()
            })
            
    except Exception as e:
        messages.error(request, f'Ошибка при добавлении в корзину: {str(e)}')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return redirect('event_detail', pk=event_id)

@login_required
@require_POST
def cart_remove(request, event_id):
    """Удаление мероприятия из корзины"""
    try:
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, event_id=event_id)
        cart_item.delete()
        
        messages.success(request, 'Мероприятие удалено из корзины')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Мероприятие удалено из корзины'
            })
            
    except Exception as e:
        messages.error(request, f'Ошибка при удалении из корзины: {str(e)}')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return redirect('cart_detail')

@login_required
@require_POST
def cart_update(request, event_id):
    """Обновление количества билетов в корзине"""
    try:
        action = request.POST.get('action')
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, event_id=event_id)
        
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        
        cart_item.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'quantity': cart_item.quantity,
                'total_price': cart_item.total_price
            })
            
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return redirect('cart_detail')



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
    """Оформление заказа из корзины"""
    try:
        cart = Cart.objects.get(user=request.user)
    
        if cart.items_count == 0:
            messages.warning(request, _("Ваша корзина пуста"))
            return redirect('cart_detail')
    
        # Проверка наличия всех билетов перед оформлением
        for item in cart.items.all():
            if item.quantity > item.event.tickets_available:
                messages.error(request, 
                    _("Для мероприятия '%(event_title)s' доступно только %(available)s билетов") % {
                        'event_title': item.event.title,
                        'available': item.event.tickets_available
                    })
                return redirect('cart_detail')
        
        # Генерация уникального номера заказа
        import uuid
        import time
        
        def generate_unique_order_number():
            timestamp = int(time.time())
            unique_id = uuid.uuid4().hex[:8].upper()
            return f"ORD-{timestamp}-{unique_id}"
        
        # Создаем заказ с уникальным номером
        order_number = generate_unique_order_number()
        
        # Проверяем, что номер действительно уникален (на всякий случай)
        while Order.objects.filter(order_number=order_number).exists():
            order_number = generate_unique_order_number()
            
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.total_price,
            status='pending',
            order_number=order_number
        )

        # Создаем элементы заказа
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                event=cart_item.event,
                quantity=cart_item.quantity,
                price=cart_item.price
            )

            # Обновляем количество доступных билетов
            event = cart_item.event
            event.tickets_available -= cart_item.quantity
            event.save()

        # Очищаем корзину
        cart.items.all().delete()

        # Сохраняем order_id в сессии для payment
        request.session['order_id'] = order.id

        messages.success(request, _("Заказ успешно создан! Перейдите к оплате."))
        return redirect('payment')
    
    except Cart.DoesNotExist:
        messages.error(request, _("Корзина не найдена"))
        return redirect('event_list')
    except Exception as e:
        messages.error(request, _("Ошибка при оформлении заказа: %(error)s") % {'error': str(e)})
        return redirect('cart_detail')
    
    # if request.method == 'POST':
    #     form = CheckoutForm(request.POST)
    #     if form.is_valid():
    #         order = form.save(commit=False)
    #         order.user = request.user
    #         order.total_amount = cart.total_price
    #         order.save()
            
    #         # Создаем элементы заказа
    #         for cart_item in cart.items.all():
    #             OrderItem.objects.create(
    #                 order=order,
    #                 event=cart_item.event,
    #                 quantity=cart_item.quantity,
    #                 price=cart_item.price # Используем цену из корзины, а не из event
    #             )
            
    #         request.session['order_id'] = order.id
    #         return redirect('payment')
    # else:
    #     form = CheckoutForm()
    
    # return render(request, 'events/checkout.html', {
    #     'cart': cart,
    #     'form': form
    # })

# @login_required
# def payment(request):
#     """Страница оплаты"""
#     try:
#         cart = get_object_or_404(Cart, user=request.user)
#         cart_items = cart.items.select_related('event').all()
        
#         if not cart_items:
#             messages.warning(request, 'Ваша корзина пуста')
#             return redirect('cart_detail')
        
#         total_amount = sum(item.total_price for item in cart_items)
        
#         # Обработка выбора способа оплаты
#         selected_method = None
#         if request.method == 'POST':
#             selected_method = request.POST.get('payment_method')
            
#             # Здесь логика обработки платежа
#             if selected_method in ['card', 'yoomoney']:
#                 # Создаем заказ
#                 order = Order.objects.create(
#                     user=request.user,
#                     total_amount=total_amount,
#                     status='pending'
#                 )
                
#                 # Добавляем items в заказ
#                 for cart_item in cart_items:
#                     order.items.create(
#                         event=cart_item.event,
#                         quantity=cart_item.quantity,
#                         price=cart_item.event.price
#                     )
                
#                 # Очищаем корзину
#                 cart.items.all().delete()
                
#                 messages.success(request, 'Заказ успешно создан! Перенаправляем на оплату...')
#                 return redirect('payment_success')
        
#         context = {
#             'cart_items': cart_items,
#             'total_amount': total_amount,
#             'selected_method': selected_method,
#         }
#         return render(request, 'events/payment.html', context)
        
#     except Exception as e:
#         messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')
#         return redirect('cart_detail')

@login_required
def payment(request):
    """Страница оплаты"""
    order_id = request.session.get('order_id')
    
    if not order_id:
        messages.error(request, _("Заказ не найден. Пожалуйста, начните оформление заказа заново."))
        return redirect('cart_detail')
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, _("Заказ не найден"))
        return redirect('cart_detail')
    
    if request.method == 'POST':
        # Обработка оплаты
        order.status = 'paid'
        order.save()
        
        # Очищаем сессию
        if 'order_id' in request.session:
            del request.session['order_id']
        
        messages.success(request, _("Оплата прошла успешно!"))
        return redirect('payment_success')
    
    context = {
        'order': order,
    }
    return render(request, 'events/payment.html', context)

@login_required
def payment_success(request):
    """Страница успешной оплаты"""
    return render(request, 'events/payment_success.html')
# def payment_success(request):
#     """Страница успешной оплаты"""
#     from django.utils import timezone
#     context = {
#         'current_date': timezone.now().strftime('%d.%m.%Y %H:%M')
#     }
#     return render(request, 'events/payment_success.html', context)

@login_required
def payment_cancel(request):
    """Страница отмены оплаты"""
    messages.info(request, _("Оплата была отменена."))
    return redirect('cart_detail')
# def payment_cancel(request):
#     """Страница отмены оплаты"""
#     messages.info(request, 'Оплата была отменена')
#     return render(request, 'events/payment_cancel.html')

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

# Подсчет общей стоимости
@property
def total_price(self):
    return sum(item.price * item.quantity for item in self.items.all())
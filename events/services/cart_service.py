from django.db import transaction
from ..models import Cart, CartItem, Event
from django.core.exceptions import ValidationError

class CartService:
    
    @staticmethod
    def get_user_cart(user):
        """Получить корзину пользователя"""
        cart, created = Cart.objects.get_or_create(user=user)
        return cart
    
    @staticmethod
    @transaction.atomic
    def add_to_cart(user, event, quantity=1):
        """Добавить товар в корзину"""
        if quantity <= 0:
            raise ValidationError("Количество должно быть положительным")
        
        if event.tickets_available < quantity:
            raise ValidationError(f"Доступно только {event.tickets_available} билетов")
        
        cart = CartService.get_user_cart(user)
        
        # Проверяем, есть ли уже этот товар в корзине
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            event=event,
            defaults={
                'quantity': quantity,
                'price': event.price
            }
        )
        
        if not created:
            # Если товар уже есть, увеличиваем количество
            new_quantity = cart_item.quantity + quantity
            if new_quantity > event.tickets_available:
                raise ValidationError(f"Нельзя добавить больше {event.tickets_available} билетов")
            
            cart_item.quantity = new_quantity
            cart_item.save()
        
        return cart_item
    
    @staticmethod
    @transaction.atomic
    def update_cart_item(user, item_id, action):
        """Обновить количество товара в корзине"""
        try:
            cart = CartService.get_user_cart(user)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            
            if action == 'increase':
                if cart_item.quantity >= cart_item.event.tickets_available:
                    raise ValidationError(f"Нельзя добавить больше {cart_item.event.tickets_available} билетов")
                cart_item.quantity += 1
            elif action == 'decrease':
                if cart_item.quantity <= 1:
                    cart_item.delete()
                    return None
                cart_item.quantity -= 1
            else:
                raise ValidationError("Неверное действие")
            
            cart_item.save()
            return cart_item
            
        except CartItem.DoesNotExist:
            raise ValidationError("Товар не найден в корзине")
    
    @staticmethod
    @transaction.atomic
    def remove_from_cart(user, item_id):
        """Удалить товар из корзины"""
        cart = CartService.get_user_cart(user)
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            return True
        except CartItem.DoesNotExist:
            raise ValidationError("Товар не найден в корзине")
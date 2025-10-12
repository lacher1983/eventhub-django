from django.db import transaction
from ..models import Cart, CartItem, Event

class CartService:
    
    @staticmethod
    def get_or_create_cart(user):
        """Получение или создание корзины"""
        cart, created = Cart.objects.get_or_create(user=user)
        return cart
    
    @staticmethod
    def add_to_cart(user, event, quantity=1):
        """Добавление в корзину"""
        cart = CartService.get_or_create_cart(user)
        
        if quantity > event.tickets_available:
            raise ValidationError(f"Доступно только {event.tickets_available} билетов")
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            event=event,
            defaults={'quantity': quantity, 'price': event.price}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item
    
    @staticmethod
    def get_cart_total(user):
        """Получение общей суммы корзины"""
        try:
            cart = Cart.objects.get(user=user)
            return cart.total_price
        except Cart.DoesNotExist:
            return 0
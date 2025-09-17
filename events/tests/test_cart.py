from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Event, Category, Cart, CartItem
from ..services.cart_service import CartService

User = get_user_model()

class CartTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            date="2025-12-31T23:59:00Z",
            location="Test Location",
            event_type="offline",
            category=self.category,
            organizer=self.user,
            price=1000.00,
            capacity=100,
            tickets_available=50
        )
    
    def test_add_to_cart(self):
        """Тест добавления товара в корзину"""
        cart_item = CartService.add_to_cart(self.user, self.event, 2)
        
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.price, 1000.00)
        self.assertEqual(cart_item.total_price, 2000.00)
        
        cart = CartService.get_user_cart(self.user)
        self.assertEqual(cart.items_count, 1)
        self.assertEqual(cart.total_price, 2000.00)
    
    def test_update_cart_item(self):
        """Тест обновления количества товара"""
        CartService.add_to_cart(self.user, self.event, 1)
        cart_item = CartService.update_cart_item(self.user, 1, 'increase')
        
        self.assertEqual(cart_item.quantity, 2)
        
        cart_item = CartService.update_cart_item(self.user, 1, 'decrease')
        self.assertEqual(cart_item.quantity, 1)
    
    def test_remove_from_cart(self):
        """Тест удаления товара из корзины"""
        CartService.add_to_cart(self.user, self.event, 1)
        result = CartService.remove_from_cart(self.user, 1)
        
        self.assertTrue(result)
        
        cart = CartService.get_user_cart(self.user)
        self.assertEqual(cart.items_count, 0)
        self.assertEqual(cart.total_price, 0)
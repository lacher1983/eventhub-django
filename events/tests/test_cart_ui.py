from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import Event, Category, Cart, CartItem

User = get_user_model()

class CartUITestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
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
    
    def test_cart_page_loads(self):
        """Тест загрузки страницы корзины"""
        # Логиним пользователя
        self.client.login(username='testuser', password='testpass123')
        
        # Добавляем товар в корзину через view
        response = self.client.post(reverse('events:add_to_cart', args=[self.event.id]), {
            'quantity': 2
        })
        
        # Проверяем страницу корзины
        response = self.client.get(reverse('events:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event")
    
    def test_cart_buttons_exist(self):
        """Тест наличия кнопок в корзине"""
        # Логиним пользователя
        self.client.login(username='testuser', password='testpass123')
        
        # Добавляем товар в корзину
        cart, created = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            event=self.event,
            quantity=2,
            price=1000.00
        )
        
        # Проверяем страницу корзины
        response = self.client.get(reverse('events:cart'))
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие кнопок по классам
        self.assertContains(response, 'decrease-quantity')
        self.assertContains(response, 'increase-quantity')
        self.assertContains(response, 'remove-item')


# from django.test import TestCase, Client
# from django.contrib.auth import get_user_model
# from django.urls import reverse
# from ..models import Event, Category, Cart, CartItem

# User = get_user_model()

# class CartUITestCase(TestCase):
    
#     def setUp(self):
#         self.client = Client()
#         self.user = User.objects.create_user(
#             username='testuser',
#             email='test@example.com',
#             password='testpass123'
#         )
        
#         self.category = Category.objects.create(
#             name="Test Category",
#             slug="test-category"
#         )
        
#         self.event = Event.objects.create(
#             title="Test Event",
#             description="Test Description",
#             date="2025-12-31T23:59:00Z",
#             location="Test Location",
#             event_type="offline",
#             category=self.category,
#             organizer=self.user,
#             price=1000.00,
#             capacity=100,
#             tickets_available=50
#         )
        
#         # Логиним пользователя
#         self.client.login(username='testuser', password='testpass123')
        
#         # Добавляем товар в корзину
#         cart, created = Cart.objects.get_or_create(user=self.user)
#         CartItem.objects.create(
#             cart=cart,
#             event=self.event,
#             quantity=2,
#             price=1000.00
#         )
    
#     def test_cart_page_loads(self):
#         """Тест загрузки страницы корзины"""
#         response = self.client.get(reverse('events:cart'))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "Test Event")
#         self.assertContains(response, "2000")
    
#     def test_cart_buttons_exist(self):
#         """Тест наличия кнопок в корзине"""
#         response = self.client.get(reverse('events:cart'))
#         self.assertContains(response, "increase-quantity")
#         self.assertContains(response, "decrease-quantity")
#         self.assertContains(response, "remove-item")
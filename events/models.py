from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from django.utils.text import slugify
from django.core.files.base import ContentFile
from PIL import Image
import io
import os
from django.contrib.auth import get_user_model

class Advertisement(models.Model):
    AD_TYPES = [
        ('banner', 'Баннер'),
        ('video', 'Видео'),
        ('popup', 'Всплывающее окно'),
        ('sidebar', 'Боковая панель'),
    ]

    POSITIONS = [
        ('top', 'Верх страницы'),
        ('sidebar', 'Боковая панель'),
        ('between_events', 'Между событиями'),
        ('bottom', 'Низ страницы'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    ad_type = models.CharField(max_length=20, choices=AD_TYPES, default='banner', verbose_name="Тип рекламы")
    position = models.CharField(max_length=20, choices=POSITIONS, default='top', verbose_name="Позиция")
    image = models.ImageField(upload_to='ads/', blank=True, null=True, verbose_name="Изображение")
    video_url = models.URLField(blank=True, null=True, verbose_name="URL видео")
    content = models.TextField(blank=True, null=True, verbose_name="Текстовое содержание")
    link = models.URLField(verbose_name="Ссылка")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    start_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    click_count = models.IntegerField(default=0, verbose_name="Клики")
    impression_count = models.IntegerField(default=0, verbose_name="Показы")
    
    class Meta:
        verbose_name = "Рекламный баннер"
        verbose_name_plural = "Рекламные баннеры"
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    def is_currently_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def increment_click(self):
        self.click_count += 1
        self.save()
    
    def increment_impression(self):
        self.impression_count += 1
        self.save()

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(unique=True, default='default-category')
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Автоматически генерим slug из name
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Event(models.Model):
    EVENT_TYPES = [
        ('online', 'Онлайн'),
        ('offline', 'Оффлайн'),
        ('hybrid', 'Гибридный'),
    ]
  
    title = models.CharField(max_length=200, verbose_name="Название мероприятия")
    description = models.TextField(verbose_name="Описание")
    short_description = models.CharField(max_length=300, verbose_name="Краткое описание", 
                                       default='Краткое описание мероприятия')
    date = models.DateTimeField(verbose_name="Дата и время")
    location = models.CharField(max_length=200, verbose_name="Место проведения")
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES, verbose_name="Тип мероприятия")
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, 
                               null=True, verbose_name="Категория")
    organizer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='organized_events', 
                                verbose_name="Организатор")
    price = models.DecimalField(max_digits=10, decimal_places=2, 
                              default=0, verbose_name="Цена")
    is_free = models.BooleanField(default=False, verbose_name="Бесплатное мероприятие")
    tickets_available = models.PositiveIntegerField(default=100, verbose_name="Доступно билетов")
    capacity = models.PositiveIntegerField(verbose_name="Вместимость", default=50)
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Дата обновления")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name="Средний рейтинг")

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ['-date']
    
    def update_average_rating(self):
        """Обновляет средний рейтинг мероприятия"""
        from django.db.models import Avg
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        self.average_rating = avg_rating or 0
        self.save(update_fields=['average_rating'])
    
    def get_user_review(self, user):
        """Получить отзыв конкретного пользователя"""
        try:
            return self.reviews.get(user=user)
        except Review.DoesNotExist:
            return None
        
    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'pk': self.pk})

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            try:
                if os.path.exists(self.image.path):
                    return self.image.url
            except:
                pass
        return f"{settings.STATIC_URL}images/default-event.jpg"

    def save(self, *args, **kwargs):
        # Создание default изображения если нет
        if not self.image:
            try:
                img = Image.new('RGB', (300, 200), color='#f0f0f0')
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG')
                self.image.save('default_event.jpg', ContentFile(img_io.getvalue()), save=False)
            except:
                pass
    
       # Ресайз изображения если нужно
        super().save(*args, **kwargs)
        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.height > 600 or img.width > 800:
                    output_size = (800, 600)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except:
                pass

    def __str__(self):
        return self.title
    
    @property
    def is_free_event(self):
        return self.price <= 0 or self.is_free
    
class Registration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждена'),
        ('cancelled', 'Отменена'),
    ]
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)  # ТОЛЬКО ОДНО поле!
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-registration_date']
        verbose_name = "Регистрация"
        verbose_name_plural = "Регистрации"

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

User = get_user_model()


class Favorite(models.Model):
    """Модель для избранных мероприятий пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="Пользователь")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorited_by', verbose_name="Мероприятие")
    registration_date = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Дата регистрации")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные мероприятия"
        unique_together = ['user', 'event']  # Один пользователь - одно избранное на событие
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


class Review(models.Model):
    """Модель отзывов и рейтингов мероприятий"""
    RATING_CHOICES = [
        (1, '⭐ - Ужасно'),
        (2, '⭐⭐ - Плохо'),
        (3, '⭐⭐⭐ - Нормально'),
        (4, '⭐⭐⭐⭐ - Хорошо'),
        (5, '⭐⭐⭐⭐⭐ - Отлично'),
    ]
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Мероприятие"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Пользователь"
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name="Рейтинг"
    )
    comment = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name="Комментарий"
    )
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ['event', 'user']  # Один пользователь - один отзыв на событие
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.rating}⭐)"
    

class Registration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждена'),
        ('cancelled', 'Отменена'),
    ]
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-registration_date']
        verbose_name = "Регистрация"
        verbose_name_plural = "Регистрации"

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"        

# монетизируемся
class Partner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    promo_code = models.CharField(max_length=20, unique=True)
    commission = models.DecimalField(max_digits=5, decimal_places=2)

# платное продвижение мероприятия 
class Promotion(models.Model):
    PROMO_TYPES = [
        ('top', 'На вершине списка'),
        ('highlight', 'Подсветка'),
        ('email', 'Email рассылка')
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    promo_type = models.CharField(max_length=20, choices=PROMO_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    from django.db import models
from decimal import Decimal

class Cart(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Корзина {self.user.username}"

    @property
    def total_price(self):
        total = 0
        for item in self.items.all():
            total += item.total_price
        return total

    @property
    def items_count(self):
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['cart', 'event']]

    def __str__(self):
        return f"{self.quantity} x {self.event.title}"

    @property
    def total_price(self):
        return self.event.price * self.quantity
    
    class Meta:
        unique_together = [['cart', 'event']]  # Один товар - одна позиция в корзине

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачено'),
        ('cancelled', 'Отменено'),
        ('refunded', 'Возврат'),
    ]

    PAYMENT_METHODS = [
        ('card', 'Банковская карта'),
        ('paypal', 'PayPal'),
        ('qiwi', 'QIWI'),
        ('yoomoney', 'ЮMoney'),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Заказ #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d')}{self.user.id:04d}"
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.event.title}"

    @property
    def total_price(self):
        return self.price * self.quantity
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from django.utils.text import slugify
from django.core.files.base import ContentFile
import io
import os
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.safestring import mark_safe

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
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def increment_click(self):
        self.click_count += 1
        self.save()
    
    def increment_impression(self):
        """Увеличивает счетчик показов"""
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
    
    # Видео поля
    video_trailer = models.FileField(
        upload_to='event_videos/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm'])],
        verbose_name="Видео-трейлер"
    )
    
    video_thumbnail = models.ImageField(
        upload_to='video_thumbnails/',
        null=True,
        blank=True,
        verbose_name="Превью видео"
    )
    
    is_background_video = models.BooleanField(
        default=False,
        verbose_name="Использовать как фоновое видео"
    )

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ['-date']
    
    def update_average_rating(self):
        from django.db.models import Avg
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        self.average_rating = avg_rating or 0
        self.save(update_fields=['average_rating'])
    
    def get_user_review(self, user):
        try:
            return self.reviews.get(user=user)
        except models.Model.DoesNotExist:  # или просто Exception
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
        if not self.image:
            try:
                img = Image.new('RGB', (300, 200), color='#f0f0f0')
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG')
                self.image.save('default_event.jpg', ContentFile(img_io.getvalue()), save=False)
            except:
                pass
    
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
    
    @property
    def has_video(self):
        return bool(self.video_trailer)
    
    @property
    def rating_stars(self):
        """Возвращает HTML со звездами рейтинга"""
        full_stars = int(self.average_rating)
        half_star = 1 if self.average_rating - full_stars >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        stars_html = []
        # Полные звезды
        stars_html.extend(['<i class="fas fa-star text-warning"></i>'] * full_stars)
        # Половина звезды
        if half_star:
            stars_html.append('<i class="fas fa-star-half-alt text-warning"></i>')
        # Пустые звезды
        stars_html.extend(['<i class="far fa-star text-warning"></i>'] * empty_stars)
        
        return mark_safe(''.join(stars_html))
    
    @property
    def dark_theme_badge(self):
        """Уникальные бейджи в стиле DarkSide"""
        if self.price == 0:
            return '<span class="badge bg-success"><i class="fas fa-gift"></i> Бесплатно</span>'
        elif self.capacity - self.registrations.count() < 10:
            return '<span class="badge bg-danger"><i class="fas fa-fire"></i> Заканчиваются</span>'
        elif self.average_rating >= 4.5:
            return '<span class="badge bg-warning text-dark"><i class="fas fa-crown"></i> Премиум</span>'
        return ''    

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

    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-registration_date']
        verbose_name = "Регистрация"
        verbose_name_plural = "Регистрации"

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="Пользователь")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorited_by', verbose_name="Мероприятие")
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные мероприятия"
        unique_together = ['user', 'event']
        ordering = ['-added_date']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

class Review(models.Model):
    RATING_CHOICES = [
        (1, '⭐ - Ужасно'),
        (2, '⭐⭐ - Плохо'),
        (3, '⭐⭐⭐ - Нормально'),
        (4, '⭐⭐⭐⭐ - Хорошо'),
        (5, '⭐⭐⭐⭐⭐ - Отлично'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews', verbose_name="Мероприятие")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Пользователь")
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="Рейтинг")
    comment = models.TextField(max_length=1000, blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ['event', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.rating}⭐)"

class Partner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    promo_code = models.CharField(max_length=20, unique=True)
    commission = models.DecimalField(max_digits=5, decimal_places=2)

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

class Cart(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def items_count(self):
        """Количество товаров в корзине"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        """Общая стоимость корзины"""
        return sum(float(item.total_price) for item in self.items.all())
    
    def __str__(self):
        return f"Корзина {self.user.username}"
    
    def update_total(self): # обновить общую сумму корзины
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total
        # from django.db.models import Sum
        # result = self.items.aggregate(total=Sum('price'))
        # self.total = result['total'] or 0
        # self.save(update_fields=['total'])

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
    
    @property
    def total_price(self):
        return float(self.price) * self.quantity # а число ли это, батенька

    def __str__(self):
        return f"{self.quantity} x {self.event.title}"

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
    
    # Добавляем поля для информации о покупателе
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.CharField(max_length=250, blank=True, verbose_name="Адрес")
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Почтовый индекс")
    country = models.CharField(max_length=100, blank=True, verbose_name="Страна")
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Временно сохраняем, чтобы получить ID
            if not self.pk:
                super().save(*args, **kwargs)
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d')}{self.id:04d}"
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
    
class VideoAd(models.Model):
    title = models.CharField(max_length=200)
    video_file = models.FileField(upload_to='video_ads/')
    thumbnail = models.ImageField(upload_to='video_thumbnails/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
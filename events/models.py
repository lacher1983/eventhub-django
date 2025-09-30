from django.db import models
from django.urls import reverse
from django.core.files.base import ContentFile
from PIL import Image
import io
import os
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from datetime import timedelta
import uuid


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
    # Группировка по категориям
    EVENT_CATEGORIES = [
        ('education', 'Образовательные'),
        ('business', 'Бизнес'),
        ('entertainment', 'Развлечения'),
        ('culture', 'Культура'),
        ('sport', 'Спорт'),
        ('social', 'Социальные'),
    ]
    
    # Детальные типы мероприятий
    EVENT_TYPES = [
        # Образовательные
        ('webinar', 'Вебинар'),
        ('workshop', 'Мастер-класс'),
        ('course', 'Курс'),
        ('lecture', 'Лекция'),
        ('training', 'Тренинг'),
        
        # Бизнес
        ('conference', 'Конференция'),
        ('business_meeting', 'Бизнес-встреча'),
        ('networking', 'Нетворкинг'),
        ('exhibition', 'Выставка'),
        
        # Развлечения
        ('concert', 'Концерт'),
        ('party', 'Вечеринка'),
        ('festival', 'Фестиваль'),
        ('show', 'Шоу'),
        
        # Культура
        ('exhibition_culture', 'Выставка (культурная)'),
        ('tour', 'Экскурсия'),
        ('master_class', 'Мастер-класс (творческий)'),
        
        # Спорт
        ('competition', 'Соревнование'),
        ('sport_event', 'Спортивное событие'),
        ('tournament', 'Турнир'),
        
        # Социальные
        ('charity', 'Благотворительное'),
        ('volunteering', 'Волонтерство'),
        ('community', 'Сообщество'),
    ]

    EVENT_FORMATS = [
        ('online', 'Онлайн'),
        ('offline', 'Оффлайн'),
        ('hybrid', 'Гибридный'),
    ]

    # Уровни сложности
    DIFFICULTY_LEVELS = [
        ('beginner', 'Для начинающих'),
        ('intermediate', 'Средний уровень'),
        ('advanced', 'Для продвинутых'),
        ('all', 'Для всех уровней'),
    ]
  
    title = models.CharField(max_length=200, verbose_name="Название мероприятия")
    description = models.TextField(verbose_name="Описание")
    short_description = models.CharField(max_length=300, verbose_name="Краткое описание", 
                                       default='Краткое описание мероприятия')
    date = models.DateTimeField(verbose_name="Дата и время")
    location = models.CharField(max_length=200, verbose_name="Место проведения")
    category = models.CharField(max_length=20, choices=EVENT_CATEGORIES, verbose_name="Категория", default='education')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name="Тип мероприятия", default='workshop')
    event_format = models.CharField(max_length=10, choices=EVENT_FORMATS, verbose_name="Формат проведения", default='offline')
    # Поля для сложности и требований
    difficulty_level = models.CharField(
        max_length=20, 
        choices=DIFFICULTY_LEVELS, 
        default='all',
        verbose_name="Уровень сложности"
    )
    requirements = models.TextField(blank=True, verbose_name="Что нужно взять с собой")
    image = models.ImageField(upload_to='events/', blank=True, null=True)
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
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, blank=True, verbose_name="Средний рейтинг")
    
    # Теги
    tags = models.ManyToManyField('Tag', blank=True, verbose_name="Теги")

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
    
       # Ресайз изображения
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
    def get_category_display_name(self):
        """Возвращает читаемое название категории"""
        return dict(self.EVENT_CATEGORIES).get(self.category, self.category)
    
    @property
    def get_type_display_name(self):
        """Возвращает читаемое название типа"""
        return dict(self.EVENT_TYPES).get(self.event_type, self.event_type)
    
    @property
    def get_difficulty_display_name(self):
        """Возвращает читаемое название уровня сложности"""
        return dict(self.DIFFICULTY_LEVELS).get(self.difficulty_level, self.difficulty_level)
    
    def get_similar_events(self):
        """Получить похожие мероприятия (по категории и типу)"""
        from django.db.models import Q
        return Event.objects.filter(
            Q(category=self.category) | Q(event_type=self.event_type),
            is_active=True
        ).exclude(pk=self.pk).distinct()[:6]


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=7, default='#007bff', verbose_name="Цвет тега")  # HEX цвет
    
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


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
    """Модель для избранных мероприятий пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="Пользователь")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorited_by', verbose_name="Мероприятие")
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)  # Персональные заметки
    registration_date = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Дата регистрации")

    class Meta:
        unique_together = ['user', 'event']  # Один пользователь может добавить событие в избранное только один раз
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные мероприятия"
        ordering = ['-registration_date', '-created_at']

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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['cart', 'event']]  # Один товар - одна позиция в корзине

    @property
    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} x {self.event.title}"

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем цену из события при сохранении
        if not self.price and self.event:
            self.price = self.event.price
        super().save(*args, **kwargs)

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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Заказ #{self.order_number} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Генерируем уникальный номер заказа
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Генерация уникального номера заказа"""
        import random
        import string
        from django.utils import timezone
        
        # Формат: ORDER-ГГММДД-XXXXX
        date_part = timezone.now().strftime('%y%m%d')
        random_part = ''.join(random.choices(string.digits, k=5))
        order_number = f"ORDER-{date_part}-{random_part}"
        
        # Проверяем уникальность
        while Order.objects.filter(order_number=order_number).exists():
            random_part = ''.join(random.choices(string.digits, k=5))
            order_number = f"ORDER-{date_part}-{random_part}"
        
        return order_number

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
    

User = get_user_model()

class EmailConfirmation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    confirmation_code = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"Confirmation for {self.user.email}"
# Подписка на мероприятия
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    categories = models.ManyToManyField(Category, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Subscription: {self.user.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'event']

# Статистика
class EventStatistic(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    views_count = models.PositiveIntegerField(default=0)
    registrations_count = models.PositiveIntegerField(default=0)
    favorites_count = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

class PlatformStatistic(models.Model):
    date = models.DateField(unique=True)
    total_users = models.PositiveIntegerField(default=0)
    total_events = models.PositiveIntegerField(default=0)
    total_registrations = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
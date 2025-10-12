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
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError

User = get_user_model()


class Advertisement(models.Model):
    AD_TYPES = [
        ('banner', _('Баннер')),
        ('video', _('Видео')),
        ('popup', _('Всплывающее окно')),
        ('sidebar', _('Боковая панель')),
    ]

    POSITIONS = [
        ('top', _('Верх страницы')),
        ('sidebar', _('Боковая панель')),
        ('between_events', _('Между событиями')),
        ('bottom', _('Низ страницы')),
    ]

    title = models.CharField(max_length=200, verbose_name=_("Название"))
    ad_type = models.CharField(max_length=20, choices=AD_TYPES, default='banner', verbose_name=_("Тип рекламы"))
    position = models.CharField(max_length=20, choices=POSITIONS, default='top', verbose_name=_("Позиция"))
    image = models.ImageField(upload_to='ads/', blank=True, null=True, verbose_name=_("Изображение"))
    video_url = models.URLField(blank=True, null=True, verbose_name="URL видео")
    content = models.TextField(blank=True, null=True, verbose_name=_("Текстовое содержание"))
    link = models.URLField(verbose_name=_("Ссылка"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    start_date = models.DateTimeField(verbose_name=_("Дата начала"))
    end_date = models.DateTimeField(verbose_name=_("Дата окончания"))
    click_count = models.IntegerField(default=0, verbose_name=_("Клики"))
    impression_count = models.IntegerField(default=0, verbose_name=_("Показы"))
    
    class Meta:
        verbose_name = _("Рекламный баннер")
        verbose_name_plural = _("Рекламные баннеры")
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
    name = models.CharField(_('название категории'), max_length=100)
    slug = models.SlugField(_('слаг'), unique=True, default='default-category')
    description = models.TextField(_('описание'), blank=True)

    class Meta:
        verbose_name = _('категория')
        verbose_name_plural = _('категории')

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
        ('education', _('Образовательные')),
        ('business', _('Бизнес')),
        ('entertainment', _('Развлечения')),
        ('culture', _('Культура')),
        ('sport', _('Спорт')),
        ('social', _('Социальные')),
    ]
    
    # Детальные типы мероприятий
    EVENT_TYPES = [
        # Образовательные
        ('webinar', _('Вебинар')),
        ('workshop', _('Мастер-класс')),
        ('course', _('Курс')),
        ('lecture', _('Лекция')),
        ('training', _('Тренинг')),
        
        # Бизнес
        ('conference', _('Конференция')),
        ('business_meeting', _('Бизнес-встреча')),
        ('networking', _('Нетворкинг')),
        ('exhibition', _('Выставка')),
        
        # Развлечения
        ('concert', _('Концерт')),
        ('party', _('Вечеринка')),
        ('festival', _('Фестиваль')),
        ('show', _('Шоу')),
        
        # Культура
        ('exhibition_culture', _('Выставка (культурная)')),
        ('tour', _('Экскурсия')),
        ('master_class', _('Мастер-класс (творческий)')),
        
        # Спорт
        ('competition', _('Соревнование')),
        ('sport_event', _('Спортивное событие')),
        ('tournament', _('Турнир')),
        
        # Социальные
        ('charity', _('Благотворительное')),
        ('volunteering', _('Волонтерство')),
        ('community', _('Сообщество')),

        # Другие
        ('trending', '🔥 Популярное'),
        ('new', '🆕 Новое'),
        ('featured', '⭐ Рекомендуемое'),
        ('early_bird', '🐦 Ранняя пташка'),
        ('last_chance', '⏰ Последний шанс'),
        ('sold_out', '🔴 Продано'),
        ('exclusive', '👑 Эксклюзив'),
        ('discount', '💸 Скидка'),
    ]

    EVENT_FORMATS = [
        ('online', _('Онлайн')),
        ('offline', _('Оффлайн')),
        ('hybrid', _('Гибридный')),
    ]

    # Уровни сложности
    DIFFICULTY_LEVELS = [
        ('beginner', _('Для начинающих')),
        ('intermediate', _('Средний уровень')),
        ('advanced', _('Для продвинутых')),
        ('all', _('Для всех уровней')),
    ]
  
    title = models.CharField(max_length=200, verbose_name=_("Название мероприятия"))
    description = models.TextField(verbose_name=_("Описание"))
    short_description = models.CharField(max_length=300, verbose_name=_("Краткое описание"), 
                                       default=_('Краткое описание мероприятия'))
    date = models.DateTimeField(verbose_name=_("Дата и время"))
    location = models.CharField(max_length=200, verbose_name=_("Место проведения"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Категория"), default='education')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name=_("Тип мероприятия"), default='workshop')
    event_format = models.CharField(max_length=10, choices=EVENT_FORMATS, verbose_name=_("Формат проведения"), default='offline')
    
    # Поля для сложности и требований
    difficulty_level = models.CharField(
        max_length=20, 
        choices=DIFFICULTY_LEVELS, 
        default='all',
        verbose_name=_("Уровень сложности")
    )
    requirements = models.TextField(blank=True, verbose_name=_("Что нужно взять с собой"))
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    organizer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='organized_events', 
                                verbose_name=_("Организатор"))
    price = models.DecimalField(max_digits=10, decimal_places=2, 
                              default=0, verbose_name=_("Цена"))
    is_free = models.BooleanField(default=False, verbose_name=_("Бесплатное мероприятие"))
    tickets_available = models.PositiveIntegerField(default=100, verbose_name=_("Доступно билетов"))
    capacity = models.PositiveIntegerField(verbose_name=_("Вместимость"), default=50)
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name=_("Дата обновления"))
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, blank=True, verbose_name=_("Средний рейтинг"))
    # новые поля для карты
    latitude = models.FloatField('Широта', null=True, blank=True)
    longitude = models.FloatField('Долгота', null=True, blank=True)
    
    # Теги
    tags = models.ManyToManyField('Tag', blank=True, verbose_name=_("Теги"))

    badges = models.JSONField(default=list, blank=True, verbose_name="Бейджи")

    class Meta:
        verbose_name = _("Мероприятие")
        verbose_name_plural = _("Мероприятия")
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
    
    # Метод проверки доступности билетов
    def is_ticket_available(self, quantity=1):
        return self.tickets_available >= quantity
    
    # Метод для бронирования билетов
    def reserve_tickets(self, quantity=1):
        if self.is_ticket_available(quantity):
            self.tickets_available -= quantity
            self.save()
            return True
        return False    

    def get_active_badges(self):
        """Динамическое определение активных бейджей"""
        active_badges = []
        
        # Проверяем условия для каждого бейджа
        if self.registrations.count() > self.capacity * 0.8:
            active_badges.append('trending')
        
        if self.created_at and (timezone.now() - self.created_at).days < 7:
            active_badges.append('new')
        
        if self.average_rating >= 4.5:
            active_badges.append('featured')
        
        if self.date and (self.date - timezone.now()).days <= 3:
            active_badges.append('last_chance')
        
        if self.registrations.count() >= self.capacity:
            active_badges.append('sold_out')
        
        if self.price == 0:
            active_badges.append('free')
        
        if self.event_format == 'online':
            active_badges.append('online')
        else:
            active_badges.append('offline')
        
        return active_badges
    

    @property
    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Название тега"))
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=7, default='#007bff', verbose_name=_("Цвет тега"))  # HEX цвет
    
    class Meta:
        verbose_name = _("Тег")
        verbose_name_plural = _("Теги")
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
        ('pending', _('Ожидает')),
        ('confirmed', _('Подтверждена')),
        ('cancelled', _('Отменена')),
    ]
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True) 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    notes = models.TextField(
        _('дополнительные заметки'),
        blank=True,
        null=True,
        help_text=_('Дополнительная информация о регистрации')
    )

    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-registration_date']
        verbose_name = _("Регистрация")
        verbose_name_plural = _("Регистрации")

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

User = get_user_model()


class Favorite(models.Model):
    """Модель для избранных мероприятий пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name=_("Пользователь"))
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorited_by', verbose_name=_("Мероприятие"))
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)  # Персональные заметки
    registration_date = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name=_("Дата регистрации"))

    class Meta:
        unique_together = ['user', 'event']  # Один пользователь может добавить событие в избранное только один раз
        verbose_name = _("Избранное")
        verbose_name_plural = _("Избранные мероприятия")
        ordering = ['-registration_date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


class Review(models.Model):
    """Модель отзывов и рейтингов мероприятий"""
    RATING_CHOICES = [
        (1, _('⭐ - Ужасно')),
        (2, _('⭐⭐ - Плохо')),
        (3, _('⭐⭐⭐ - Нормально')),
        (4, _('⭐⭐⭐⭐ - Хорошо')),
        (5, _('⭐⭐⭐⭐⭐ - Отлично')),
    ]
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("Мероприятие")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("Пользователь")
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Рейтинг")
    )
    comment = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name=_("Комментарий")
    )
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата обновления")
    )

    class Meta:
        verbose_name = _("Отзыв")
        verbose_name_plural = _("Отзывы")
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
        ('top', _('На вершине списка')),
        ('highlight', _('Подсветка')),
        ('email', _('Email рассылка'))
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
    def items_count(self):
        return self.items.count()

    @property
    def total_price(self):
        total = 0
        for item in self.items.all():
            total += item.total_price
        return total


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
        ('pending', _('Ожидает оплаты')),
        ('paid', _('Оплачено')),
        ('cancelled', _('Отменено')),
        ('refunded', _('Возврат')),
    ]

    PAYMENT_METHODS = [
        ('card', _('Банковская карта')),
        ('paypal', _('PayPal')),
        ('qiwi', _('QIWI')),
        ('yoomoney', _('ЮMoney')),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
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


class ExternalEventSource(models.Model):
    """Источники внешних мероприятий"""
    name = models.CharField(max_length=100, verbose_name=_("Название источника"))
    url = models.URLField(verbose_name=_("URL источника"))
    parser_config = models.JSONField(default=dict, verbose_name=_("Конфигурация парсера"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name=_("Последняя синхронизация"))
    
    class Meta:
        verbose_name = _("Источник мероприятий")
        verbose_name_plural = _("Источники мероприятий")
    
    def __str__(self):
        return self.name


class ExternalEvent(models.Model):
    """Внешние мероприятия с других платформ"""
    source = models.ForeignKey(ExternalEventSource, on_delete=models.CASCADE, verbose_name=_("Источник"))
    external_id = models.CharField(max_length=100, verbose_name=_("Внешний ID"))
    title = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(verbose_name=_("Описание"))
    short_description = models.CharField(max_length=300, verbose_name=_("Краткое описание"))
    date = models.DateTimeField(verbose_name=_("Дата и время"))
    location = models.CharField(max_length=200, verbose_name=_("Место проведения"))
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Цена"))
    is_free = models.BooleanField(default=False, verbose_name=_("Бесплатное"))
    image_url = models.URLField(blank=True, null=True, verbose_name=_("URL изображения"))
    external_url = models.URLField(verbose_name=_("URL на внешнем сайте"))
    category = models.CharField(max_length=50, verbose_name=_("Категория"))
    is_archived = models.BooleanField(default=False, verbose_name=_("В архиве"))
    raw_data = models.JSONField(default=dict, verbose_name=_("Сырые данные"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Внешнее мероприятие")
        verbose_name_plural = _("Внешние мероприятия")
        unique_together = ['source', 'external_id']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} ({self.source.name})"
    
    @property
    def is_past_event(self):
        """Проверяет, прошло ли мероприятие"""
        return self.date < timezone.now()
    
    def archive(self):
        """Перемещает мероприятие в архив"""
        self.is_archived = True
        self.save()


class TravelBuddyGroup(models.Model):
    """Группа попутчиков для мероприятия"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='buddy_groups')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    name = models.CharField(max_length=200, verbose_name=_('Название группы'))
    description = models.TextField(verbose_name=_('Описание группы'))
    max_members = models.PositiveIntegerField(default=10, verbose_name=_('Максимальное количество участников'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активная группа'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Группа попутчиков')
        verbose_name_plural = _('Группы попутчиков')

    def __str__(self):
        return f"{self.name} - {self.event.title}"

    def current_members_count(self):
        return self.members.count()

    def available_slots(self):
        return self.max_members - self.current_members_count()

    def is_full(self):
        return self.current_members_count() >= self.max_members

class TravelBuddyMembership(models.Model):
    """Участник группы попутчиков"""
    group = models.ForeignKey(TravelBuddyGroup, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True, verbose_name=_('Утвержден'))

    class Meta:
        verbose_name = _('Участник группы')
        verbose_name_plural = _('Участники групп')
        unique_together = ['group', 'user']

class TravelBuddyMessage(models.Model):
    """Сообщение в чате группы"""
    group = models.ForeignKey(TravelBuddyGroup, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_messages')
    message = models.TextField(verbose_name=_('Сообщение'))
    created_at = models.DateTimeField(auto_now_add=True)
    is_system_message = models.BooleanField(default=False, verbose_name=_('Системное сообщение'))

    class Meta:
        verbose_name = _('Сообщение группы')
        verbose_name_plural = _('Сообщения групп')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"

# class BuddyRequest(models.Model):
#     GENDER_CHOICES = [
#         ('any', 'Любой'),
#         ('male', 'Мужской'),
#         ('female', 'Женский'),
#         ('individual', _('Индивидуальный попутчик')),
#         ('group', _('Группа')),
#         ('any', _('Любой вариант')),
#     ]   

#     REQUEST_TYPES = [
#         ('travel', 'Попутчик для поездки'),
#         ('accommodation', 'Совместное проживание'),
#         ('both', 'Попутчик и проживание'),
#     ]

#     STATUS_CHOICES = [
#         ('active', 'Активный'),
#         ('fulfilled', 'Найден попутчик'),
#         ('cancelled', 'Отменен'),
#     ]

#     event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name=_('Мероприятие'))
#     user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('Пользователь'))
#     message = models.TextField(verbose_name=_('Сообщение'), blank=True)
#     request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, default='travel', verbose_name=_('Тип запроса'))
#     description = models.TextField(verbose_name=_('Описание запроса'))
#     max_group_size = models.PositiveIntegerField(default=1, verbose_name=_('Максимальный размер группы'))
#     is_active = models.BooleanField(default=True, verbose_name=_('Активен'))
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Создан'))
#     preferred_gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='any', verbose_name=_('Предпочтительный пол'))
#     max_buddies = models.PositiveIntegerField(default=1, verbose_name=_('Максимальное количество попутчиков'))
#     updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Обновлен'))
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name=_('Статус'))
    
#     class Meta:
#         verbose_name = _('Запрос попутчика')
#         verbose_name_plural = _('Запросы попутчиков')
#         ordering = ['-created_at']
    
#     def __str__(self):
#         return f"{self.user.username} - {self.event.title}"

User = get_user_model()

class ChatSession(models.Model):
    """Сессия чата пользователя с ботом"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    context = models.JSONField(default=dict, blank=True)  # Контекст разговора
    
    class Meta:
        verbose_name = 'Сессия чата'
        verbose_name_plural = 'Сессии чата'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Чат {self.user.username} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"

class ChatMessage(models.Model):
    """Сообщения в чате"""
    MESSAGE_TYPES = [
        ('user', 'Пользователь'),
        ('assistant', 'Ассистент'),
        ('system', 'Система'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)  # Дополнительные данные
    
    class Meta:
        verbose_name = 'Сообщение чата'
        verbose_name_plural = 'Сообщения чата'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."

class ChatIntent(models.Model):
    """Интенты (намерения) для NLP"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    patterns = models.JSONField(default=list)  # Паттерны фраз для этого интента
    responses = models.JSONField(default=list)  # Возможные ответы
    action = models.CharField(max_length=200, blank=True)  # Действие (например, 'search_events')
    required_entities = models.JSONField(default=list)  # Необходимые сущности
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Интент чата'
        verbose_name_plural = 'Интенты чата'
    
    def __str__(self):
        return self.name

class ChatEntity(models.Model):
    """Сущности для извлечения из сообщений"""
    name = models.CharField(max_length=50, unique=True)
    patterns = models.JSONField(default=list)  # Регулярные выражения для извлечения
    examples = models.JSONField(default=list)  # Примеры значений
    
    class Meta:
        verbose_name = 'Сущность чата'
        verbose_name_plural = 'Сущности чата'
    
    def __str__(self):
        return self.name
    

# Геймификация модели
class Achievement(models.Model):
    """Достижения пользователей"""
    ACHIEVEMENT_TYPES = [
        ('event', 'Мероприятия'),
        ('social', 'Социальные'),
        ('exploration', 'Исследование'),
        ('mastery', 'Мастерство'),
        ('special', 'Особые'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    icon = models.CharField(max_length=50, default='🏆')  # Emoji или класс иконки
    points = models.PositiveIntegerField(default=10)
    requirement = models.JSONField(default=dict)  # Условия получения
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['points', 'name']
    
    def __str__(self):
        return f"{self.icon} {self.name}"

class UserAchievement(models.Model):
    """Достижения полученные пользователями"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    progress = models.FloatField(default=0.0)
    is_unlocked = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Достижение пользователя'
        verbose_name_plural = 'Достижения пользователей'
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        status = "Разблокировано" if self.is_unlocked else f"Прогресс: {self.progress*100}%"
        return f"{self.user.username} - {self.achievement.name} ({status})"

class LevelSystem(models.Model):
    """Система уровней пользователей"""
    level = models.PositiveIntegerField(unique=True)
    level_name = models.CharField(max_length=50)
    min_points = models.PositiveIntegerField()
    max_points = models.PositiveIntegerField()
    badge_icon = models.CharField(max_length=50, default='⭐')
    color = models.CharField(max_length=7, default='#667eea')
    benefits = models.JSONField(default=list)
    
    class Meta:
        verbose_name = 'Уровень системы'
        verbose_name_plural = 'Уровни системы'
        ordering = ['level']
    
    def __str__(self):
        return f"Уровень {self.level}: {self.level_name}"

class UserProfile(models.Model):
    """Расширенный профиль пользователя с игровыми метриками"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='game_profile')
    total_points = models.PositiveIntegerField(default=0)
    current_level = models.ForeignKey(LevelSystem, on_delete=models.SET_NULL, null=True, blank=True)
    streak_days = models.PositiveIntegerField(default=0)  # Дней подряд активности
    last_activity = models.DateTimeField(auto_now=True)
    badges = models.JSONField(default=list)  # Список бейджей
    stats = models.JSONField(default=dict)  # Статистика пользователя
    
    class Meta:
        verbose_name = 'Игровой профиль'
        verbose_name_plural = 'Игровые профили'
    
    def __str__(self):
        return f"Профиль {self.user.username} (Уровень {self.current_level.level if self.current_level else 0})"
    
    def update_stats(self):
        """Обновление статистики пользователя"""
        from .models import Event, Registration, Review, Favorite
        
        self.stats = {
            'events_created': self.user.organized_events.count(),
            'events_attended': Registration.objects.filter(user=self.user).count(),
            'reviews_written': Review.objects.filter(user=self.user).count(),
            'favorites_added': Favorite.objects.filter(user=self.user).count(),
            'days_active': self._calculate_active_days(),
            'categories_explored': self._calculate_categories_explored(),
        }
        self.save()
    
    def _calculate_active_days(self):
        """Расчет количества активных дней"""
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        activities = Registration.objects.filter(
            user=self.user,
            registration_date__gte=thirty_days_ago
        ).dates('registration_date', 'day').distinct()
        return len(activities)
    
    def _calculate_categories_explored(self):
        """Расчет количества исследованных категорий"""
        from .models import Registration
        categories = Registration.objects.filter(
            user=self.user
        ).values_list('event__category__name', flat=True).distinct()
        return len([cat for cat in categories if cat])

class Leaderboard(models.Model):
    """Таблица лидеров"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leaderboard_position')
    position = models.PositiveIntegerField()
    points = models.PositiveIntegerField()
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Позиция в таблице лидеров'
        verbose_name_plural = 'Таблица лидеров'
        ordering = ['position']
    
    def __str__(self):
        return f"#{self.position} {self.user.username} ({self.points} очков)"

class Quest(models.Model):
    """Ежедневные и еженедельные задания"""
    QUEST_TYPES = [
        ('daily', 'Ежедневное'),
        ('weekly', 'Еженедельное'),
        ('monthly', 'Ежемесячное'),
        ('special', 'Специальное'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    quest_type = models.CharField(max_length=10, choices=QUEST_TYPES)
    points_reward = models.PositiveIntegerField()
    requirement = models.JSONField(default=dict)  # Требования для выполнения
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['quest_type', 'points_reward']
    
    def __str__(self):
        return f"{self.name} ({self.get_quest_type_display()})"

class UserQuest(models.Model):
    """Прогресс пользователя по заданиям"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quests')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    progress = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Задание пользователя'
        verbose_name_plural = 'Задания пользователей'
        unique_together = ['user', 'quest']
    
    def __str__(self):
        status = "Выполнено" if self.is_completed else f"Прогресс: {self.progress*100}%"
        return f"{self.user.username} - {self.quest.name} ({status})"
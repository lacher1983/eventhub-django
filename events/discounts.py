from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid

class Discount(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Процентная скидка'),
        ('fixed', 'Фиксированная сумма'),
        ('free', 'Бесплатное участие'),
    ]
    
    code = models.CharField(max_length=20, unique=True, verbose_name="Промокод")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, verbose_name="Тип скидки")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Значение скидки")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Минимальная сумма заказа")
    max_uses = models.PositiveIntegerField(default=1, verbose_name="Максимум использований")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Количество использований")
    start_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    applicable_events = models.ManyToManyField('Event', blank=True, verbose_name="Применимые мероприятия")
    
    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"
    
    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"
    
    def is_valid(self):
        """Проверка валидности скидки"""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            self.used_count < self.max_uses
        )
    
    def calculate_discount(self, order_amount):
        """Расчет суммы скидки"""
        if not self.is_valid():
            return 0
        
        if order_amount < self.min_order_amount:
            return 0
        
        if self.discount_type == 'percentage':
            return (order_amount * self.value) / 100
        elif self.discount_type == 'fixed':
            return min(self.value, order_amount)
        elif self.discount_type == 'free':
            return order_amount
        
        return 0
    
    def apply_discount(self):
        """Применение скидки"""
        if self.is_valid():
            self.used_count += 1
            self.save()
            return True
        return False

class DiscountService:
    @staticmethod
    def validate_discount(code, order_amount, event=None):
        """Валидация скидки"""
        try:
            discount = Discount.objects.get(code=code, is_active=True)
            
            if not discount.is_valid():
                return None, "Скидка недействительна"
            
            if order_amount < discount.min_order_amount:
                return None, f"Минимальная сумма заказа {discount.min_order_amount}"
            
            if event and discount.applicable_events.exists():
                if not discount.applicable_events.filter(id=event.id).exists():
                    return None, "Скидка не применима к этому мероприятию"
            
            return discount, None
        
        except Discount.DoesNotExist:
            return None, "Скидка не найдена"
    
    @staticmethod
    def generate_discount_code(length=8):
        """Генерация уникального промокода"""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not Discount.objects.filter(code=code).exists():
                return code
    
    @staticmethod
    def create_percentage_discount(percentage, max_uses=100, days_valid=30):
        """Создание процентной скидки"""
        code = DiscountService.generate_discount_code()
        return Discount.objects.create(
            code=code,
            discount_type='percentage',
            value=percentage,
            max_uses=max_uses,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=days_valid)
        )
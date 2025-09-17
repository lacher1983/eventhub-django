from django.core.management.base import BaseCommand
from accounts.models import User
from events.models import Cart

class Command(BaseCommand):
    help = 'Создает корзины для всех существующих пользователей'

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            cart, created = Cart.objects.get_or_create(user=user)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создана корзина для пользователя {user.username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Корзина для пользователя {user.username} уже существует')
                )
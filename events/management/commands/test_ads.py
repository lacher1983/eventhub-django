from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Test command for management commands'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show verbose output',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(' Запуск тестовой команды в verbose режиме')
            self.stdout.write('Проверка работы management commands...')
        
        self.stdout.write(
            self.style.SUCCESS(' Тестовая команда успешно выполнена!')
        )
        
        if verbose:
            self.stdout.write(' Система команд работает корректно')
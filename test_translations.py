import os
import django
import sys
from pathlib import Path

print("=== Starting Translation Test ===")

# Добавляем текущую директорию в Python path
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path}")

try:
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

from django.utils import translation
from django.utils.translation import gettext as _
from django.conf import settings

def test_all():
    print("\n=== CHECKING SETTINGS ===")
    print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"LANGUAGE_CODE: {getattr(settings, 'LANGUAGE_CODE', 'NOT SET')}")
    print(f"LANGUAGES: {getattr(settings, 'LANGUAGES', 'NOT SET')}")
    print(f"LOCALE_PATHS: {getattr(settings, 'LOCALE_PATHS', 'NOT SET')}")
    
    print("\n=== CHECKING FILES ===")
    locale_path = current_dir / 'locale'
    print(f"Locale path exists: {locale_path.exists()}")
    
    if locale_path.exists():
        for lang in ['en', 'ru']:
            mo_file = locale_path / lang / 'LC_MESSAGES' / 'django.mo'
            po_file = locale_path / lang / 'LC_MESSAGES' / 'django.po'
            print(f"\n{lang.upper()}:")
            print(f"  .mo: {mo_file.exists()} ({mo_file})")
            print(f"  .po: {po_file.exists()} ({po_file})")
    else:
        print("✗ Locale folder does not exist!")
    
    print("\n=== TESTING TRANSLATIONS ===")
    test_phrases = ['Мероприятия', 'Создать мероприятие', 'Войти']
    
    for lang in ['ru', 'en']:
        print(f"\n--- {lang.upper()} ---")
        try:
            translation.activate(lang)
            print(f"Active language: {translation.get_language()}")
            
            for phrase in test_phrases:
                translated = _(phrase)
                status = "✓" if translated != phrase or lang == 'ru' else "✗"
                print(f"  {status} '{phrase}' -> '{translated}'")
        except Exception as e:
            print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    test_all()
    print("\n=== TEST COMPLETE ===")
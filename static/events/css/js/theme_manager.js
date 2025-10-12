class ThemeManager {
    constructor() {
        this.currentTheme = this.getSavedTheme() || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.setupEventListeners();
        this.addThemeClassToBody();
    }

    setupEventListeners() {
        // Кнопка переключения темы
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Системные предпочтения
        this.watchSystemPreference();
    }

    getSavedTheme() {
        return localStorage.getItem('eventhub-theme');
    }

    saveTheme(theme) {
        localStorage.setItem('eventhub-theme', theme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.saveTheme(theme);
        this.updateToggleButton();
        this.dispatchThemeChangeEvent();
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    updateToggleButton() {
        const toggle = document.getElementById('theme-toggle');
        if (!toggle) return;

        const sunIcon = toggle.querySelector('.sun-icon');
        const moonIcon = toggle.querySelector('.moon-icon');

        if (this.currentTheme === 'dark') {
            sunIcon.style.opacity = '0';
            moonIcon.style.opacity = '1';
        } else {
            sunIcon.style.opacity = '1';
            moonIcon.style.opacity = '0';
        }
    }

    watchSystemPreference() {
        // Следим за изменениями системной темы
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        const handleSystemThemeChange = (e) => {
            // Применяем системную тему только если пользователь не выбрал свою
            if (!this.getSavedTheme()) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        };

        mediaQuery.addEventListener('change', handleSystemThemeChange);
        
        // Инициализация при загрузке
        if (!this.getSavedTheme()) {
            this.applyTheme(mediaQuery.matches ? 'dark' : 'light');
        }
    }

    addThemeClassToBody() {
        document.body.classList.add('theme-loaded');
    }

    dispatchThemeChangeEvent() {
        const event = new CustomEvent('themeChanged', {
            detail: { theme: this.currentTheme }
        });
        document.dispatchEvent(event);
    }

    // Методы для програмного управления темой
    setLightTheme() {
        this.applyTheme('light');
    }

    setDarkTheme() {
        this.applyTheme('dark');
    }

    getCurrentTheme() {
        return this.currentTheme;
    }

    // Для синхронизации темы между вкладками
    setupCrossTabSync() {
        window.addEventListener('storage', (e) => {
            if (e.key === 'eventhub-theme' && e.newValue) {
                this.applyTheme(e.newValue);
            }
        });
    }
}

// Инициализация темы
document.addEventListener('DOMContentLoaded', function() {
    window.themeManager = new ThemeManager();
    window.themeManager.setupCrossTabSync();
});

// API для использования в других скриптах
window.ThemeManager = ThemeManager;
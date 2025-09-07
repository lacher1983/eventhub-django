from django.contrib import admin
from .models import Event, Category, Registration, Review, Favorite
from config.admin_customization import admin_site  

@admin.register(Event, site=admin_site)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'date', 'location', 'event_type', 'is_active', 'price', 'is_free', 'tickets_available', 'created_at']
    list_editable = ['price', 'is_free', 'tickets_available']
    list_filter = ['event_type', 'is_active', 'category', 'date', 'is_free', 'created_at']
    search_fields = ('title', 'description', 'location', 'organizer__username')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('title', 'short_description', 'description', 'category')
        }),
        ('Дата и время', {
            'fields': ('date',)
        }),
        ('Место проведения', {
            'fields': ('location', 'event_type')
        }),
        ('Организационная информация', {
            'fields': ('organizer', 'price', 'capacity', 'is_active')
        }),
        ('Изображение', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
    )
    
    def is_upcoming(self, obj):
        return obj.is_upcoming()
    is_upcoming.boolean = True
    is_upcoming.short_description = 'Предстоящее'
    
    def get_organizer_name(self, obj):
        return obj.organizer.username
    get_organizer_name.short_description = 'Организатор'
    
    def get_average_rating(self, obj):
        return obj.average_rating or 'Нет оценок'
    get_average_rating.short_description = 'Рейтинг'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'rating', 'registration_date']
    list_filter = ['rating', 'registration_date']
    search_fields = ['event__title', 'user__username', 'comment']
    readonly_fields = ['registration_date', 'updated_at']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'registration_date']
    list_filter = ['registration_date']
    search_fields = ['user__username', 'event__title']
    readonly_fields = ['registration_date']

@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

@admin.register(Registration, site=admin_site)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registration_date', 'status')
    list_filter = ('status', 'registration_date', 'event')
    search_fields = ('user__username', 'event__title')
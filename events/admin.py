from django.contrib import admin
from .models import Event, Category, Registration, Review, Favorite  

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'date', 'location', 'price', 'is_active', 'created_at', 'get_organizer_name', 'get_average_rating']
    list_filter = ['is_active', 'event_type', 'category', 'date', 'created_at']
    search_fields = ['title', 'description', 'location']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_organizer_name(self, obj):
        return obj.organizer.username
    get_organizer_name.short_description = 'Организатор'
    
    def get_average_rating(self, obj):
        return obj.average_rating or 'Нет оценок'
    get_average_rating.short_description = 'Рейтинг'

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'registered_at', 'is_confirmed']
    list_filter = ['is_confirmed', 'registered_at']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['event__title', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'event__title']
    readonly_fields = ['created_at']
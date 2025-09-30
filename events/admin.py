from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Event, Tag, Registration, Category, Favorite, Review, Advertisement, Cart, CartItem, Order, OrderItem
from config.admin_customization import admin_site


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'colored_tag']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def colored_tag(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.color, obj.name
        )
    colored_tag.short_description = 'Вид тега'

class CategoryFilter(admin.SimpleListFilter):
    title = 'Категория'
    parameter_name = 'category'
    
    def lookups(self, request, model_admin):
        return Event.EVENT_CATEGORIES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category=self.value())
        return queryset
    
class TypeFilter(admin.SimpleListFilter):
    title = 'Тип мероприятия'
    parameter_name = 'event_type'
    
    def lookups(self, request, model_admin):
        return Event.EVENT_TYPES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(event_type=self.value())
        return queryset

@admin.register(Event, site=admin_site)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_category_display', 'get_event_type_display', 'organizer', 'date', 'location', 'event_format', 'is_active', 'price', 'is_free', 'tickets_available', 'created_at']
    list_editable = ['price', 'is_free', 'tickets_available']
    list_filter = ['event_format', 'difficulty_level', 'is_active', 'category', 'date', 'is_free', 'created_at']
    search_fields = ('title', 'description', 'location', 'organizer__username')
    filter_horizontal = ['tags']
    list_per_page = 20
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'short_description', 'description', 'image', 'tags')
        }),
        ('Классификация', {
            'fields': ('category', 'event_type', 'event_format', 'difficulty_level')
        }),
        ('Дата и место', {
            'fields': ('date', 'location', 'requirements')
        }),
        ('Организация и билеты', {
            'fields': ('organizer', 'capacity', 'tickets_available')
        }),
        ('Стоимость', {
            'fields': ('price', 'is_free')
        }),
        ('Статус', {
            'fields': ('is_active', 'average_rating')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'average_rating']
    
    def get_category_display(self, obj):
        return obj.get_category_display_name
    get_category_display.short_description = 'Категория'

    def get_event_type_display(self, obj):
        return obj.get_type_display_name
    get_event_type_display.short_description = 'Тип мероприятия'

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


@admin.register(Registration, site=admin_site)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registration_date', 'status')
    list_filter = ('status', 'registration_date', 'event')
    search_fields = ('user__username', 'event__title')


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'registration_date']
    list_filter = ['registration_date']
    search_fields = ['user__username', 'event__title']
    readonly_fields = ['registration_date']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'rating', 'registration_date']
    list_filter = ['rating', 'registration_date']
    search_fields = ['event__title', 'user__username', 'comment']
    readonly_fields = ['registration_date', 'updated_at']


@admin.register(Advertisement, site=admin_site)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'ad_type', 'is_active')



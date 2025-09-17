from django.contrib import admin
from .models import Event, Category, Registration, Review, Favorite, Advertisement
from .models import Cart, CartItem, Order, OrderItem
from config.admin_customization import admin_site  

@admin.register(Event, site=admin_site)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'date', 'is_active', 'price', 'is_free', 'tickets_available', 'has_video', 'is_background_video']
    list_editable = ['price', 'is_free', 'tickets_available', 'is_background_video']
    list_filter = ['is_background_video','event_type', 'is_active', 'category', 'date', 'is_free']
    search_fields = ('title', 'description')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'short_description', 'description', 'category', 'organizer', 'capacity', 'is_active')
        }),
        ('Дата и время', {
            'fields': ('date',)
        }),
        ('Место проведения', {
            'fields': ('location', 'event_type')
        }),
        ('Медиа контент', {
            'fields': ('image', 'video_trailer', 'video_thumbnail', 'is_background_video')
        }),
        ('Цена и билеты', {
            'fields': ('price', 'is_free', 'tickets_available')
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
    list_display = ['event', 'user', 'rating']
    list_filter = ['rating'] 
    search_fields = ['event__title', 'user__username', 'comment']
    readonly_fields = []

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'event']
    list_filter = []
    search_fields = ['user__username', 'event__title']
    readonly_fields = []

@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'description']

@admin.register(Registration, site=admin_site)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registration_date', 'status')
    list_filter = ('status', 'registration_date', 'event')
    search_fields = ('user__username', 'event__title')
    readonly_fields = ['registration_date']

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title']

@admin.register(Cart, site=admin_site)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']

@admin.register(CartItem, site=admin_site)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'event', 'quantity', 'price']

@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_amount', 'status', 'created_at']

@admin.register(OrderItem, site=admin_site)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'event', 'quantity', 'price']
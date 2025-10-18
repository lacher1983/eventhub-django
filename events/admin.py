from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (Event, Tag, Registration, Category, Favorite, Review, 
    Advertisement, Cart, CartItem, Order, OrderItem, 
    ExternalEventSource, ExternalEvent,
    PromoVideo, ProjectPromoVideo, 
    # TravelBuddyGroup, TravelBuddyMembership, TravelBuddyMessage, BuddyRequest,
    EmailConfirmation, Subscription, Notification, EventStatistic, PlatformStatistic)
from config.admin_customization import admin_site


@admin.register(Tag, site=admin_site)
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

@admin.register(Favorite, site=admin_site)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'registration_date']
    list_filter = ['registration_date']
    search_fields = ['user__username', 'event__title']
    readonly_fields = ['registration_date']


@admin.register(Review, site=admin_site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'rating', 'registration_date']
    list_filter = ['rating', 'registration_date']
    search_fields = ['event__title', 'user__username', 'comment']
    readonly_fields = ['registration_date', 'updated_at']


@admin.register(Advertisement, site=admin_site)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'ad_type', 'is_active')


@admin.register(ExternalEventSource, site=admin_site)
class ExternalEventSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'last_sync']
    list_filter = ['is_active']
    actions = ['sync_selected_sources']
    
    def sync_selected_sources(self, request, queryset):
        from django.core.management import call_command
        for source in queryset:
            call_command('sync_external_events', f'--source={source.id}')
        self.message_user(request, "Синхронизация запущена")
    sync_selected_sources.short_description = "Синхронизировать выбранные источники"

@admin.register(ExternalEvent, site=admin_site)
class ExternalEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'date', 'location', 'is_free', 'is_archived']
    list_filter = ['source', 'is_archived', 'is_free', 'category']
    search_fields = ['title', 'location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PromoVideo, site=admin_site)
class PromoVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'video_source', 'view_count', 'is_main_promo', 'created_at']
    list_filter = ['video_source', 'is_main_promo', 'created_at']
    search_fields = ['title', 'event__title']
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    list_editable = ['is_main_promo']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'event', 'is_main_promo', 'display_order')
        }),
        ('Видео контент', {
            'fields': ('video_source', 'youtube_url', 'vimeo_url', 'external_url', 'uploaded_video')
        }),
        ('Дополнительно', {
            'fields': ('thumbnail', 'duration', 'autoplay', 'view_count')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event')
    
@admin.register(ProjectPromoVideo, site=admin_site)
class ProjectPromoVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'video_type', 'is_active', 'show_on_homepage', 'view_count', 'created_at']
    list_filter = ['video_type', 'is_active', 'show_on_homepage', 'created_at']
    list_editable = ['is_active', 'show_on_homepage']
    search_fields = ['title', 'description']
    readonly_fields = ['view_count', 'click_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'video_type')
        }),
        ('Видео контент', {
            'fields': ('youtube_url', 'thumbnail')
        }),
        ('Настройки отображения', {
            'fields': ('is_active', 'show_on_homepage', 'show_on_landing', 'autoplay', 'display_order')
        }),
        ('Статистика', {
            'fields': ('view_count', 'click_count'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# @admin.register(TravelBuddyGroup, site=admin_site)
# class TravelBuddyGroupAdmin(admin.ModelAdmin):
#     list_display = ['name', 'event', 'creator', 'current_members_count', 'is_active', 'created_at']
#     list_filter = ['is_active', 'created_at']
#     search_fields = ['name', 'event__title', 'creator__username']

# @admin.register(TravelBuddyMembership, site=admin_site)
# class TravelBuddyMembershipAdmin(admin.ModelAdmin):
#     list_display = ['group', 'user', 'joined_at', 'is_approved']
#     list_filter = ['is_approved', 'joined_at']
#     search_fields = ['group__name', 'user__username']

# @admin.register(TravelBuddyMessage, site=admin_site)
# class TravelBuddyMessageAdmin(admin.ModelAdmin):
#     list_display = ['user', 'group', 'message_short', 'created_at', 'is_system_message']
#     list_filter = ['is_system_message', 'created_at']
#     search_fields = ['user__username', 'group__name', 'message']
    
#     def message_short(self, obj):
#         return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
#     message_short.short_description = 'Сообщение'

# @admin.register(BuddyRequest, site=admin_site)
# class BuddyRequestAdmin(admin.ModelAdmin):
#     list_display = ['user', 'event', 'request_type', 'is_active', 'created_at']
#     list_filter = ['request_type', 'is_active', 'created_at']
#     search_fields = ['user__username', 'event__title', 'description']

# Дополнительные модели 
@admin.register(EmailConfirmation, site=admin_site)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ['user', 'confirmed', 'created_at']
    list_filter = ['confirmed', 'created_at']
    readonly_fields = ['confirmation_code', 'created_at']

@admin.register(Subscription, site=admin_site)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    filter_horizontal = ['categories']

@admin.register(Notification, site=admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'sent_at', 'read']
    list_filter = ['read', 'sent_at']
    readonly_fields = ['sent_at']

@admin.register(EventStatistic, site=admin_site)
class EventStatisticAdmin(admin.ModelAdmin):
    list_display = ['event', 'views_count', 'registrations_count', 'favorites_count', 'last_updated']
    readonly_fields = ['last_updated']

@admin.register(PlatformStatistic, site=admin_site)
class PlatformStatisticAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_users', 'total_events', 'total_registrations', 'active_users']
    readonly_fields = ['date']

# Модели корзины и заказов
@admin.register(Cart, site=admin_site)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'total_price', 'created_at']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CartItem, site=admin_site)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'event', 'quantity', 'price', 'total_price']
    list_filter = ['added_at']
    
    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = 'Общая стоимость'

@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    search_fields = ['order_number', 'user__username']

@admin.register(OrderItem, site=admin_site)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'event', 'quantity', 'price', 'total_price']
    
    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = 'Общая стоимость'
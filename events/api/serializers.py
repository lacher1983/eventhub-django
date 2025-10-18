
from rest_framework import serializers
from ..models import Event, Favorite, Category, Review, Registration
from accounts.models import User  

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'registration_date']
        read_only_fields = ['user', 'registration_date']

class EventSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    is_favorite = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'short_description', 'description',
            'date', 'location', 'event_type', 'price', 'capacity',
            'category', 'image', 'average_rating', 'reviews',
            'is_favorite', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False

class FavoriteSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'event', 'created_at']

class RegistrationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.date', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)
    event_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Registration
        fields = [
            'id', 'event', 'event_title', 'event_date', 'event_location', 
            'event_image', 'registration_date', 'status'
        ]
        read_only_fields = ['registration_date', 'status']

    def get_event_image(self, obj):
        request = self.context.get('request')
        if obj.event.image:
            return request.build_absolute_uri(obj.event.image.url) if request else obj.event.image.url
        return None
from rest_framework import serializers
from ..models import Registration, Event, Category, Review, Favorite

class RegistrationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.date', read_only=True)
    
    class Meta:
        model = Registration
        fields = ['id', 'event', 'event_title', 'event_date', 'user', 'registration_date', 'status']
        read_only_fields = ['user', 'registration_date']

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
            'is_favorite', 'registration_date'
        ]
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False

class FavoriteSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'event', 'registration_date']
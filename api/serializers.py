from rest_framework import serializers
from django.contrib.auth.models import User
from users.models import Profile
from listings.models import Listing, ListingImage, Favorite
from categories.models import Category
from msgs_app.models import Message
from ratings.models import Rating


# ── Auth / Users ──────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(write_only=True)
    city = serializers.CharField(required=False, allow_blank=True)
    profile_type = serializers.ChoiceField(choices=Profile.USER_TYPE_CHOICES, default='person')
    display_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'phone', 'city', 'profile_type', 'display_name')

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        city = validated_data.pop('city', '')
        profile_type = validated_data.pop('profile_type', 'person')
        display_name = validated_data.pop('display_name', '')

        user = User.objects.create_user(**validated_data)
        profile = user.profile
        profile.phone = phone
        profile.city = city
        profile.profile_type = profile_type
        if display_name:
            profile.display_name = display_name
        profile.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = Profile
        fields = ('id', 'username', 'email', 'phone', 'city', 'avatar',
                  'profile_type', 'display_name', 'theme', 'email_verified')
        read_only_fields = ('email_verified',)

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'email' in user_data:
            instance.user.email = user_data['email']
            instance.user.save()
        return super().update(instance, validated_data)


# ── Listings ──────────────────────────────────────────────────────────────────

class ListingImageSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ListingImage
        fields = ('id', 'image', 'thumbnail_url', 'is_main')

    def get_thumbnail_url(self, obj):
        return obj.thumbnail_url


class ListingSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source='author.profile.get_display_name', read_only=True)
    author_avatar = serializers.ImageField(source='author.profile.avatar', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    is_favorite = serializers.SerializerMethodField()
    created_at_formatted = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = Listing
        fields = (
            'id', 'external_id', 'title', 'description', 'price',
            'category', 'category_name', 'category_slug',
            'author', 'author_name', 'author_avatar',
            'status', 'is_completed', 'is_promoted', 'is_sticky', 'is_urgent',
            'created_at', 'created_at_formatted', 'expiry_date',
            'total_views', 'today_views', 'images', 'is_favorite', 'parameters',
        )
        read_only_fields = (
            'id', 'external_id', 'author', 'status', 'created_at',
            'total_views', 'today_views', 'is_favorite',
        )

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, listing=obj).exists()
        return False


class FavoriteSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'listing', 'created_at')


# ── Categories ────────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'parent', 'image_url', 'children', 'view_mode', 'order')

    def get_children(self, obj):
        return CategorySerializer(obj.children.all(), many=True).data

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


# ── Messages ──────────────────────────────────────────────────────────────────

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.profile.get_display_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.profile.get_display_name', read_only=True)
    created_at_formatted = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = Message
        fields = (
            'id', 'listing', 'sender', 'sender_name',
            'recipient', 'recipient_name', 'text',
            'created_at', 'created_at_formatted', 'is_read', 'parent',
        )
        read_only_fields = ('id', 'sender', 'is_read', 'created_at')


class ConversationSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField()
    listing_title = serializers.CharField()
    other_user_id = serializers.IntegerField()
    other_user_name = serializers.CharField()
    last_message = MessageSerializer()
    unread_count = serializers.IntegerField()


# ── Ratings ───────────────────────────────────────────────────────────────────

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ('rater', 'rated_user', 'score', 'created_at', 'updated_at')
        read_only_fields = ('rater', 'created_at', 'updated_at')
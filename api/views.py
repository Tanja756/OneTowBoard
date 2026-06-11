from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import date
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ProfileSerializer,
    ListingSerializer,
    ListingImageSerializer,
    FavoriteSerializer,
    CategorySerializer,
    MessageSerializer,
    ConversationSerializer,
)
from listings.models import Listing, ListingImage, Favorite
from categories.models import Category
from users.models import Profile
from msgs_app.models import Message
from ratings.models import Rating


# ── Auth / Users ──────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_or_email = attrs.get(self.username_field)
        user = User.objects.filter(email=username_or_email).first()
        if user:
            attrs[self.username_field] = user.username
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


# ── Listings ──────────────────────────────────────────────────────────────────

class ListingListCreateView(generics.ListCreateAPIView):
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Listing.objects.filter(status='active', is_completed=False)
        queryset = queryset.filter(Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today()))

        # Фильтры
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__username=author)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        price_min = self.request.query_params.get('price_min')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)

        price_max = self.request.query_params.get('price_max')
        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by('-is_sticky', '-is_urgent', ordering)
        return queryset.select_related('author__profile', 'category').prefetch_related('images')

    def perform_create(self, serializer):
        from datetime import date, timedelta
        listing = serializer.save(author=self.request.user, status='moderation')
        # Устанавливаем срок публикации: +30 дней по умолчанию
        listing.expiry_date = date.today() + timedelta(days=30)
        # Параметры категории из тела запроса (с префиксом param_)
        param_data = {}
        for key, value in self.request.data.items():
            if key.startswith('param_'):
                slug = key[6:]
                if value:
                    param_data[slug] = value
        listing.parameters = param_data
        listing.save(update_fields=['expiry_date', 'parameters'])


class ListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.author and not self.request.user.is_staff:
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        listing = self.get_object()
        if request.user != listing.author and not request.user.is_staff:
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.author and not request.user.is_staff:
        return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    listing.is_completed = True
    listing.save()
    return Response({'status': 'completed'})


# ── User Listings ────────────────────────────────────────────────────────────

class UserListingView(generics.ListAPIView):
    serializer_class = ListingSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        username = self.kwargs['username']
        return Listing.objects.filter(
            author__username=username, status='active', is_completed=False
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
        ).select_related('author__profile', 'category').prefetch_related('images')\
         .order_by('-is_sticky', '-is_urgent', '-created_at')


# ── Favorites ─────────────────────────────────────────────────────────────────

class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related(
            'listing__author__profile', 'listing__category'
        ).prefetch_related('listing__images')

    def perform_create(self, serializer):
        listing_id = self.request.data.get('listing')
        listing = get_object_or_404(Listing, pk=listing_id)
        serializer.save(user=self.request.user, listing=listing)


class FavoriteDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        listing_id = kwargs.get('pk')
        Favorite.objects.filter(user=request.user, listing_id=listing_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True)
    serializer_class = CategorySerializer


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'


# ── Messages ──────────────────────────────────────────────────────────────────

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            Q(sender=self.request.user, is_sender_deleted=False) |
            Q(recipient=self.request.user, is_recipient_deleted=False)
        ).select_related('sender__profile', 'recipient__profile', 'listing')

    def perform_create(self, serializer):
        listing_id = self.request.data.get('listing')
        recipient_id = self.request.data.get('recipient')
        listing = get_object_or_404(Listing, pk=listing_id)
        recipient = get_object_or_404(User, pk=recipient_id)
        serializer.save(sender=self.request.user, listing=listing, recipient=recipient)


class ConversationListView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        messages_qs = Message.objects.filter(
            Q(sender=request.user, is_sender_deleted=False) |
            Q(recipient=request.user, is_recipient_deleted=False)
        ).select_related('sender__profile', 'recipient__profile', 'listing').order_by('-created_at')

        conversations = {}
        for msg in messages_qs:
            other_user = msg.recipient if msg.sender == request.user else msg.sender
            key = (msg.listing_id, other_user.id)
            if key not in conversations:
                conversations[key] = {
                    'listing_id': msg.listing_id,
                    'listing_title': msg.listing.title,
                    'other_user_id': other_user.id,
                    'other_user_name': other_user.profile.get_display_name(),
                    'last_message': msg,
                    'unread_count': 0,
                }
            else:
                if msg.created_at > conversations[key]['last_message'].created_at:
                    conversations[key]['last_message'] = msg
            if msg.recipient == request.user and not msg.is_read:
                conversations[key]['unread_count'] += 1

        serializer = ConversationSerializer(list(conversations.values()), many=True)
        return Response(serializer.data)


class ConversationDetailView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        listing_id = self.kwargs['listing_id']
        user_id = self.kwargs['user_id']
        user = self.request.user
        qs = Message.objects.filter(
            listing_id=listing_id,
            sender__in=[user.id, user_id],
            recipient__in=[user.id, user_id],
        ).filter(
            Q(sender=user, is_sender_deleted=False) |
            Q(recipient=user, is_recipient_deleted=False)
        ).order_by('created_at')
        # Отмечаем прочитанными
        qs.filter(recipient=user, is_read=False).update(is_read=True)
        return qs


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def delete_conversation(request, listing_id, user_id):
    Message.objects.filter(
        listing_id=listing_id, sender=request.user, recipient_id=user_id
    ).update(is_sender_deleted=True)
    Message.objects.filter(
        listing_id=listing_id, sender_id=user_id, recipient=request.user
    ).update(is_recipient_deleted=True)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Image Upload ──────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_listing_image(request, listing_pk):
    """Загрузка одного изображения для объявления."""
    listing = get_object_or_404(Listing, pk=listing_pk)
    if request.user != listing.author and not request.user.is_staff:
        return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    file = request.FILES.get('image')
    if not file:
        return Response({'error': 'Не передано изображение'}, status=status.HTTP_400_BAD_REQUEST)

    is_main = request.data.get('is_main', False)
    if isinstance(is_main, str):
        is_main = is_main.lower() in ('true', '1', 'yes')

    # Создаём запись изображения
    img = ListingImage(listing=listing, image=file, is_main=is_main)
    img.save()

    serializer = ListingImageSerializer(img, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_listing_image(request, listing_pk, image_pk):
    """Удаление изображения объявления."""
    listing = get_object_or_404(Listing, pk=listing_pk)
    if request.user != listing.author and not request.user.is_staff:
        return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    img = get_object_or_404(ListingImage, pk=image_pk, listing=listing)
    img.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Ratings ───────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def rate_user(request, username):
    rated_user = get_object_or_404(User, username=username)
    if request.user == rated_user:
        return Response({'error': 'Нельзя оценить себя'}, status=400)
    if not request.user.profile.email_verified:
        return Response({'error': 'Email не подтверждён'}, status=403)

    score = request.data.get('score')
    try:
        score = int(score)
        if score < 1 or score > 5:
            raise ValueError
    except (ValueError, TypeError):
        return Response({'error': 'Оценка должна быть от 1 до 5'}, status=400)

    rating, created = Rating.objects.update_or_create(
        rater=request.user,
        rated_user=rated_user,
        defaults={'score': score},
    )
    return Response({
        'average': Rating.get_average_for_user(rated_user),
        'count': Rating.get_count_for_user(rated_user),
        'my_rating': score,
    })


@api_view(['GET'])
def get_user_rating(request, username):
    user = get_object_or_404(User, username=username)
    return Response({
        'average': Rating.get_average_for_user(user),
        'count': Rating.get_count_for_user(user),
        'my_rating': Rating.get_user_rating(user, request.user) if request.user.is_authenticated else None,
    })
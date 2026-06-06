from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.ProfileRetrieveUpdateView.as_view(), name='profile'),

    # Listings
    path('listings/', views.ListingListCreateView.as_view(), name='listing_list'),
    path('listings/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('listings/<int:pk>/complete/', views.complete_listing, name='listing_complete'),
    path('listings/user/<str:username>/', views.UserListingView.as_view(), name='user_listings'),

    # Favorites
    path('favorites/', views.FavoriteListCreateView.as_view(), name='favorite_list'),
    path('favorites/<int:pk>/', views.FavoriteDestroyView.as_view(), name='favorite_delete'),

    # Images
    path('listings/<int:listing_pk>/images/', views.upload_listing_image, name='upload_image'),
    path('listings/<int:listing_pk>/images/<int:image_pk>/', views.delete_listing_image, name='delete_image'),

    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),

    # Messages
    path('messages/', views.ConversationListView.as_view(), name='conversation_list'),
    path('messages/send/', views.MessageListCreateView.as_view(), name='send_message'),
    path('messages/conversation/<int:listing_id>/<int:user_id>/',
         views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('messages/conversation/<int:listing_id>/<int:user_id>/delete/',
         views.delete_conversation, name='delete_conversation'),

    # Ratings
    path('ratings/<str:username>/', views.get_user_rating, name='get_rating'),
    path('ratings/<str:username>/rate/', views.rate_user, name='rate_user'),
]
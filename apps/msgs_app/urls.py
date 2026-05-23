from django.urls import path
from . import views
from . import api_views

app_name = 'msgs_app'

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('send/<int:listing_id>/', views.send_message_view, name='send'),
    path('reply/<int:message_id>/', views.reply_message_view, name='reply'),
    path('conversation/<int:listing_id>/<int:user_id>/', views.conversation_view, name='conversation'),
    path('delete/<int:listing_id>/<int:user_id>/', views.delete_conversation_view, name='delete_conversation'),
    # API
    path('api/unread-count/', api_views.unread_count_api, name='unread_count_api'),
]

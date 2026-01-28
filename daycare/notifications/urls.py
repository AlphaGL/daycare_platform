from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('<int:pk>/', views.message_detail, name='detail'),
    path('compose/', views.compose_message, name='compose'),
    path('announcements/', views.announcements, name='announcements'),
]
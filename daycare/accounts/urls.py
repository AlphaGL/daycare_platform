"""
URL patterns for accounts app
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.parent_register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('check-in-code/', views.update_check_in_code, name='check_in_code'),
]
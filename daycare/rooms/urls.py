from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.room_list, name='list'),
    path('<int:pk>/', views.room_detail, name='detail'),
    path('create/', views.room_create, name='create'),
    path('<int:pk>/update/', views.room_update, name='update'),
]
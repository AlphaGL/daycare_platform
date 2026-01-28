from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='list'),
    path('<int:pk>/', views.student_detail, name='detail'),
    path('register/', views.student_register, name='register'),
    path('create/', views.student_create, name='create'),
    path('<int:pk>/update/', views.student_update, name='update'),
]
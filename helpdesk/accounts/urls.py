from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # Admin user management (use /manage/ to avoid conflict with Django admin)
    path('manage/users/', views.user_list_view, name='user_list'),
    path('manage/users/create/', views.user_create_view, name='user_create'),
    path('manage/users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('manage/users/<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
]

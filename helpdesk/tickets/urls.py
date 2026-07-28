from django.urls import path
from . import views
from .health import HealthCheckView

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health_check'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.dashboard_view, name='home'),

    # Tickets
    path('tickets/', views.ticket_list_view, name='ticket_list'),
    path('tickets/create/', views.ticket_create_view, name='ticket_create'),
    path('tickets/<str:ticket_id>/', views.ticket_detail_view, name='ticket_detail'),
    path('tickets/<str:ticket_id>/update/', views.ticket_update_view, name='ticket_update'),
    path('tickets/<str:ticket_id>/delete/', views.ticket_delete_view, name='ticket_delete'),

    # Categories (Admin) - use /manage/ to avoid Django admin conflict
    path('manage/categories/', views.category_list_view, name='category_list'),
    path('manage/categories/create/', views.category_create_view, name='category_create'),
    path('manage/categories/<int:category_id>/update/', views.category_update_view, name='category_update'),
    path('manage/categories/<int:category_id>/delete/', views.category_delete_view, name='category_delete'),

    # SLA (Admin)
    path('manage/sla/', views.sla_list_view, name='sla_list'),
    path('manage/sla/create/', views.sla_form_view, name='sla_create'),
    path('manage/sla/<int:pk>/edit/', views.sla_form_view, name='sla_edit'),

    # Reports
    path('reports/', views.reports_view, name='reports'),
    path('reports/<str:report_type>/', views.reports_detail_view, name='reports_detail'),

    # AI Chat
    path('ai-chat/', views.ai_chat_view, name='ai_chat'),

    # Notification Test
    path('notifications-test/', views.notification_test_view, name='notification_test'),

    # Assign workflow
    path('assign/', views.assign_list_view, name='assign_list'),
    path('assign/<str:ticket_id>/check/', views.assign_check_view, name='assign_check'),
    path('assign/<str:ticket_id>/send/', views.assign_send_view, name='assign_send'),
    path('assign/<str:ticket_id>/status/', views.ticket_assignment_status, name='ticket_assignment_status'),

    # REST API
    path('api/tickets/', views.api_ticket_list, name='api_ticket_list'),
    path('api/tickets/<str:ticket_id>/', views.api_ticket_detail, name='api_ticket_detail'),
    path('api/tickets/<str:ticket_id>/comments/', views.api_ticket_comments, name='api_ticket_comments'),
]

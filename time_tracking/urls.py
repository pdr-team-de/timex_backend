from django.urls import path
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from rest_framework.decorators import api_view
from . import views

urlpatterns = [
    path('', views.redirect_to_appropriate_page, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    path('tracking/', views.time_tracking_view, name='time-tracking'),
    path('dashboard/admin/', views.AdminDashboard.as_view(), name='admin-dashboard'),  
    path('dashboard/admin/project_manager_dashboard', views.ProjectManagerDashboard.as_view(), name='project-manager-dashboard'),  
    path('dashboard/admin/create-admin/', views.create_admin, name='create-admin'),  
    path('dashboard/admin/project-manager/', views.create_project_manager, name='create-project-manager'), 
    path('dashboard/admin/temp-worker/', views.create_temp_worker, name='create-temp-worker'),  
    path('dashboard/admin/temp-firm/', views.create_temp_firm, name='create-temp-firm'),  
    path('dashboard/admin/station/', views.create_station, name='create-station'),  
    path('dashboard/admin/stations/', views.stations_overview, name='stations-overview'),
    path('api/station/<int:station_id>/edit/', views.edit_station, name='edit-station'),
    path('api/station/<int:station_id>/delete/', views.delete_station, name='delete-station'),

    path('project-manager/dashboard/', 
         views.ProjectManagerDashboard.as_view(),
         name='project_manager_dashboard'),

    path('api/user-time-entries/<int:user_id>/', views.get_user_time_entries, name='user-time-entries'),
    path('api/user/<int:user_id>/edit/', views.edit_user, name='edit-user'),
    path('api/user/<int:user_id>/delete/', views.delete_user, name='delete-user'),

    #path('api/time-entries/', views.create_time_entry, name='create-time-entry'),
    path('api/time-entries/', views.create_time_entry, name='create-time-entry'),

    path('api/export-time-entries/', views.export_time_entries, name='export-time-entries'),
    path('api/worker/<int:worker_id>/toggle-status/', 
         views.toggle_worker_status, 
         name='toggle-worker-status'),
    path('api/time-entry/<int:entry_id>/approve/', 
         views.approve_time_entry, 
         name='approve-time-entry'),

    path('api/worker/<int:worker_id>/status/', 
         views.get_worker_status, 
         name='worker-status'),
    path('api/worker/<int:worker_id>/activity-log/', 
         views.get_worker_activity_log, 
         name='worker-activity-log'),

    path('privacy/', views.privacy_policy, name='privacy'),
    path('imprint/', views.imprint, name='imprint'),
]
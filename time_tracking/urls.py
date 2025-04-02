from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.redirect_to_appropriate_page, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('tracking/', views.time_tracking_view, name='time-tracking'),
    path('dashboard/admin/', views.AdminDashboard.as_view(), name='admin-dashboard'),  # Changed
    path('dashboard/admin/', views.ProjectManagerDashboard.as_view(), name='project-manager-dashboard'),  # Changed
    path('dashboard/admin/project-manager/', views.create_project_manager, name='create-project-manager'),  # Changed
    path('dashboard/admin/temp-worker/', views.create_temp_worker, name='create-temp-worker'),  # Changed
    path('dashboard/admin/temp-firm/', views.create_temp_firm, name='create-temp-firm'),  # Changed
    path('project-manager/dashboard/', 
         views.ProjectManagerDashboard.as_view(),
         name='project_manager_dashboard'),
    path('generate-password/', views.generate_password_view, name='generate-password'),
    path('api/user-time-entries/<int:user_id>/', views.get_user_time_entries, name='user-time-entries'),
    path('api/time-entries/', views.create_time_entry, name='create-time-entry'),
    path('api/export-time-entries/', views.export_time_entries, name='export-time-entries'),
    path('api/worker/<int:worker_id>/toggle-status/', 
         views.toggle_worker_status, 
         name='toggle-worker-status'),
    path('api/time-entry/<int:entry_id>/approve/', 
         views.approve_time_entry, 
         name='approve-time-entry'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('imprint/', views.imprint, name='imprint'),
]
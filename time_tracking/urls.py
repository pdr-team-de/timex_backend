from django.urls import path
from . import views

urlpatterns = [
    path('tracking/', views.time_tracking_view, name='time_tracking'),
    path('create-temp-worker/', views.create_temp_worker, name='create-temp-worker'),
    path('project-manager/dashboard/', 
         views.ProjectManagerDashbaord.as_view(),  # Note: Fix typo in class name if needed
         name='project-manager-dashboard'),
    path('admin/dashboard/', views.AdminDashboard.as_view(), name='admin-dashboard'),
]
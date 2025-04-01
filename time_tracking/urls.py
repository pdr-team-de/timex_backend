from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.redirect_to_appropriate_page, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('tracking/', views.time_tracking_view, name='time-tracking'),
    path('dashboard/admin/', views.AdminDashboard.as_view(), name='admin-dashboard'),  # Changed
    path('dashboard/admin/project-manager/', views.create_project_manager, name='create-project-manager'),  # Changed
    path('dashboard/admin/temp-worker/', views.create_temp_worker, name='create-temp-worker'),  # Changed
    path('project-manager/dashboard/', 
         views.ProjectManagerDashbaord.as_view(),
         name='project-manager-dashboard'),
]
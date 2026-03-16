from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/register/', views.auth_register,  name='auth_register'),
    path('auth/login/',    views.auth_login,     name='auth_login'),
    path('auth/logout/',   views.auth_logout,    name='auth_logout'),
    path('report/',                views.report_disaster, name='report_disaster'),
    path('disasters/',             views.view_disasters,  name='view_disasters'),
    path('disasters/<int:pk>/',    views.disaster_detail, name='disaster_detail'),
    path('missing/report/', views.report_missing, name='report_missing'),
    path('missing/view/',   views.view_missing,   name='view_missing'),
    path('missing/<int:pk>/update-status/', views.update_missing_status, name='update_missing_status'),
    path('injured/report/', views.report_injured, name='report_injured'),
    path('injured/view/',   views.view_injured,   name='view_injured'),
    path('injured/<int:pk>/update-status/', views.update_injured_status, name='update_injured_status'),
    path('heatmap/',         views.disaster_heatmap, name='disaster_heatmap'),
    path('api/heatmap-data/', views.heatmap_data,   name='heatmap_data'),
    path('donate/',              views.donate,             name='donate'),
    path('feedback/',            views.submit_feedback,    name='feedback'),
    path('feedback/<int:pk>/resolve/', views.resolve_feedback, name='resolve_feedback'),
    path('admin-dashboard/',     views.admin_dashboard,    name='admin_dashboard'),
    path('get-live-population/', views.get_live_population, name='get_live_population'),
]
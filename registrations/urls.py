from django.urls import path
from . import views


app_name = 'registrations'

urlpatterns = [
    path('manage/', views.RegistrationManagementView.as_view(), name='manage'),
    path('success/', views.registration_success, name='success'),
    path('cancel/', views.registration_cancel, name='cancel'),

    # API endpoints
    path('api/by-league/<int:league_id>/', views.get_registrations_by_league, name='get_registrations_by_league'),
]   
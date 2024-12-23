from django.urls import path
from . import views


app_name = 'registrations'

urlpatterns = [
    path('manage/', views.RegistrationManagementView.as_view(), name='manage'),
    path('success/', views.registration_success, name='success'),
    path('cancel/', views.registration_cancel, name='cancel'),
]   
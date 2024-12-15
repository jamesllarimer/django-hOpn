from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('free-agent/register/<int:league_id>/', views.FreeAgentRegistrationView.as_view(), name='free_agent_registration'),
    path('free-agent/registration/success/', views.FreeAgentRegistrationSuccessView.as_view(), name='free_agent_registration_success'),
    path('free-agent/pool/<int:league_id>/', views.FreeAgentPoolView.as_view(), name='free_agent_pool'),
    path('free-agent/<int:agent_id>/details/', views.FreeAgentDetailView.as_view(), name='free_agent_details'),
    path('my-registrations/', views.MyFreeAgentRegistrationsView.as_view(), name='my_free_agent_registrations'),
]
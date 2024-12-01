from django.shortcuts import redirect
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
app_name = "sportsSignUp"
urlpatterns = [
    path("", views.index, name="index"),
    path('active-leagues/', views.active_leagues, name='active_leagues'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('leagues/', views.LeagueListView.as_view(), name='league_list'),
    path('leagues/<int:league_id>/register/free-agent/', 
         views.FreeAgentRegistrationView.as_view(), 
         name='free_agent_registration'),
    path('registration/success/', 
         views.registration_success, 
         name='registration_success'),
    path('registration/cancel/', 
         views.registration_cancel, 
         name='registration_cancel'),
    path('registrations/manage/', 
        views.RegistrationManagementView.as_view(), 
        name='registration_management'),
         
]
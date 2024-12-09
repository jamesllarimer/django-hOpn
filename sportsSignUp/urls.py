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

    path('api/teams-by-league/<int:league_id>/', 
        views.get_teams_by_league, 
        name='get_teams_by_league'),

     path('api/registrations-by-league/<int:league_id>/',
          views.get_registrations_by_league,
         name='get_registrations_by_league'),

    path('registrations/assign-team/<int:player_id>/', 
        views.assign_team, 
        name='assign_team'),

    path('api/divisions-by-league/<int:league_id>/', 
        views.get_divisions_by_league, 
        name='get_divisions_by_league'),

    path('api/teams-by-division/<int:division_id>/', 
        views.get_teams_by_division, 
        name='get_teams_by_division'),

    path('api/divisions-and-teams-by-league/<int:league_id>/', 
        views.divisions_and_teams_by_league, 
        name='divisions_and_teams_by_league'),

    path('teams/manage/', 
         views.TeamManagementView.as_view(), 
         name='team_management'),

    path('teams/<int:pk>/edit/',        
         views.TeamEditView.as_view(), 
         name='team_edit'),

    path('teams/<int:team_id>/send-email/', 
         views.send_team_email, 
         name='team_email'),

    path('teams/signup/success/', 
         views.team_signup_success, 
         name='team_signup_success'),

    path('teams/signup/<str:signup_code>/', 
         views.team_signup_page, 
         name='team_signup'),
    path('free-agent/register/<int:league_id>/', views.FreeAgentRegistrationView.as_view(), name='free_agent_registration'),
    path('free-agent/invite/<int:free_agent_id>/', views.InviteFreeAgentView.as_view(), name='invite_free_agent'),
    path('invitation/<int:invitation_id>/accept/', views.AcceptInvitationView.as_view(), name='accept_invitation'),
    path('league/<int:league_id>/free-agents/', views.FreeAgentPoolView.as_view(), name='free_agent_pool'),
    path('free-agent/<int:agent_id>/details/', views.FreeAgentDetailView.as_view(), name='free_agent_details'),
    path('teams/', views.TeamDashboardView.as_view(), name='team_dashboard'),
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('teams/claim/<int:team_id>/', views.ClaimTeamCaptainView.as_view(), name='claim_team_captain'),
    path('teams/remove-player/<int:player_id>/', views.RemovePlayerView.as_view(), name='remove_player'),
    path('teams/cancel-invitation/<int:invitation_id>/', views.CancelInvitationView.as_view(), name='cancel_invitation'),
]
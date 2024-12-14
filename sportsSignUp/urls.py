from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
app_name = "sportsSignUp"

urlpatterns = [
     # Home and Authentication
     path("", views.index, name="index"),
     path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
     path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
     path("signup/", views.SignUpView.as_view(), name="signup"),
     path('profile/manage/', views.ProfileManagementView.as_view(), name='profile_management'),

     # League and Registration
     path("active-leagues/", views.active_leagues, name="active_leagues"),
     path("leagues/", views.LeagueListView.as_view(), name="league_list"),
     path("leagues/<int:league_id>/register/free-agent/", views.FreeAgentRegistrationView.as_view(), name="free_agent_registration"),
     path("registration/success/", views.registration_success, name="registration_success"),
     path("registration/cancel/", views.registration_cancel, name="registration_cancel"),
     path("registrations/manage/", views.RegistrationManagementView.as_view(), name="registration_management"),
     path("my-free-agent-registrations/", views.MyFreeAgentRegistrationsView.as_view(), name="my_free_agent_registrations"),

     # Invitations
     path("invitation/<int:invitation_id>/decline/", views.DeclineInvitationView.as_view(), name="decline_invitation"),
     path("invitation/<int:invitation_id>/accept/", views.AcceptInvitationView.as_view(), name="accept_invitation"),
     path("free-agent/invite/<int:free_agent_id>/", views.InviteFreeAgentView.as_view(), name="invite_free_agent"),
     path("teams/sent-invitations/", views.SentInvitationsView.as_view(), name="sent_invitations"),
     path("teams/cancel-invitation/<int:invitation_id>/", views.CancelInvitationView.as_view(), name="cancel_invitation"),

     # API Endpoints
     path("api/teams-by-league/<int:league_id>/", views.get_teams_by_league, name="get_teams_by_league"),
     path("api/registrations-by-league/<int:league_id>/", views.get_registrations_by_league, name="get_registrations_by_league"),
     path("api/divisions-by-league/<int:league_id>/", views.get_divisions_by_league, name="get_divisions_by_league"),
     path("api/teams-by-division/<int:division_id>/", views.get_teams_by_division, name="get_teams_by_division"),
     path("api/divisions-and-teams-by-league/<int:league_id>/", views.divisions_and_teams_by_league, name="divisions_and_teams_by_league"),

     # Teams
     path("teams/manage/", views.TeamManagementView.as_view(), name="team_management"),
     path("teams/<int:pk>/edit/", views.TeamEditView.as_view(), name="team_edit"),
     path("teams/<int:team_id>/send-email/", views.send_team_email, name="team_email"),
     path("teams/signup/success/", views.team_signup_success, name="team_signup_success"),
     path("teams/signup/<str:signup_code>/", views.team_signup_page, name="team_signup"),
     path("teams/", views.TeamDashboardView.as_view(), name="team_dashboard"),
     path("teams/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
     path("teams/claim/<int:team_id>/", views.ClaimTeamCaptainView.as_view(), name="claim_team_captain"),
     path("teams/remove-player/<int:player_id>/", views.RemovePlayerView.as_view(), name="remove_player"),

     # Free Agents
     path("league/<int:league_id>/free-agents/", views.FreeAgentPoolView.as_view(), name="free_agent_pool"),
     path("free-agent/<int:agent_id>/details/", views.FreeAgentDetailView.as_view(), name="free_agent_details"),
     path("free-agent/register/<int:league_id>/", views.FreeAgentRegistrationView.as_view(), name="free_agent_registration"),
]

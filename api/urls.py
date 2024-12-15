from django.urls import path
from .endpoints import leagues, teams, players, divisions, registrations

app_name = 'api'

urlpatterns = [
    # League-related endpoints
    path('leagues/<int:league_id>/divisions/', 
         divisions.get_divisions_by_league, 
         name='league_divisions'),
    path('leagues/<int:league_id>/teams/', 
         teams.get_teams_by_league, 
         name='league_teams'),
    path('leagues/<int:league_id>/registrations/', 
         registrations.get_registrations_by_league, 
         name='league_registrations'),
    path('leagues/<int:league_id>/registration-stats/', 
         registrations.get_registration_stats, 
         name='league_registration_stats'),
    path('leagues/<int:league_id>/divisions-teams/', 
         divisions.get_divisions_and_teams, 
         name='league_divisions_teams'),

    # Division-related endpoints
    path('divisions/<int:division_id>/', 
         divisions.get_division_details, 
         name='division_details'),
    path('divisions/<int:division_id>/teams/', 
         teams.get_teams_by_division, 
         name='division_teams'),

    # Team-related endpoints
    path('teams/<int:team_id>/players/', 
         players.get_team_players, 
         name='team_players'),
    path('teams/<int:team_id>/assign-player/', 
         teams.assign_player, 
         name='team_assign_player'),
    path('teams/<int:team_id>/remove-player/<int:player_id>/', 
         teams.remove_player, 
         name='team_remove_player'),

    # Player-related endpoints
    path('players/<int:player_id>/assign-team/', 
         players.assign_team, 
         name='assign_player_team'),
    path('free-agents/league/<int:league_id>/', 
         players.get_free_agents, 
         name='league_free_agents'),
    path('free-agents/<int:agent_id>/', 
         players.get_free_agent_details, 
         name='free_agent_details'),

    # Registration-related endpoints
    path('registrations/<int:registration_id>/update-status/', 
         registrations.update_registration_status, 
         name='update_registration_status'),
]
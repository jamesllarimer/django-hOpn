from django.urls import path
from . import views

app_name = 'leagues'

urlpatterns = [
    path('', views.LeagueListView.as_view(), name='league_list'),
    path('active/', views.active_leagues, name='active_leagues'),

    # API endpoints for league data
    path('api/divisions/<int:league_id>/', views.get_divisions_by_league, name='get_divisions_by_league'),
    path('api/divisions-teams/<int:league_id>/', views.divisions_and_teams_by_league, name='divisions_and_teams_by_league'),
]
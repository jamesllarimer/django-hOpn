from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.TeamDashboardView.as_view(), name='dashboard'),
    path('manage/', views.TeamManagementView.as_view(), name='manage'),
    path('<int:pk>/edit/', views.TeamEditView.as_view(), name='edit'),
    path('<int:pk>/', views.TeamDetailView.as_view(), name='detail'),
    path('claim/<int:team_id>/', views.ClaimTeamCaptainView.as_view(), name='claim_captain'),
    path('remove-player/<int:player_id>/', views.RemovePlayerView.as_view(), name='remove_player'),
]
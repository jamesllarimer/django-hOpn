from django.urls import path
from . import views

app_name = 'invitations'

urlpatterns = [
    path('sent/', views.SentInvitationsView.as_view(), name='sent_invitations'),
    path('send/<int:free_agent_id>/', views.InviteFreeAgentView.as_view(), name='invite_free_agent'),
    path('<int:invitation_id>/accept/', views.AcceptInvitationView.as_view(), name='accept'),
    path('<int:invitation_id>/decline/', views.DeclineInvitationView.as_view(), name='decline'),
    path('<int:invitation_id>/cancel/', views.CancelInvitationView.as_view(), name='cancel'),
]
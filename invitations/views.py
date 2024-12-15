from datetime import timezone
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.http import JsonResponse

from .models import TeamInvitation, TeamInvitationNotification
from .forms import TeamInvitationForm, InvitationFilterForm
from players.models import FreeAgent
from teams.models import Team
from api.client import ApiClient
logger = logging.getLogger(__name__)

class InviteFreeAgentView(LoginRequiredMixin, View):
    def post(self, request, free_agent_id):
        # Get the free agent
        free_agent = get_object_or_404(FreeAgent, id=free_agent_id)
        
        # First, check if the user is a captain
        if not request.user.is_team_captain():
            return JsonResponse({
                'status': 'error',
                'message': 'You must be a team captain to invite free agents'
            }, status=403)
            
        # Get the team(s) where this user is captain
        captained_teams = Team.objects.filter(
            captain__user=request.user,
            league=free_agent.league  # Make sure the team is in the same league
        )
        
        if not captained_teams.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'No team found in this league where you are captain'
            }, status=400)
        
        team = captained_teams.first()
        
        # Check if an invitation already exists
        existing_invitation = TeamInvitation.objects.filter(
            team=team,
            free_agent=free_agent
        ).first()
        
        if existing_invitation:
            if existing_invitation.status == 'PENDING':
                return JsonResponse({
                    'status': 'error',
                    'message': 'An invitation is already pending for this free agent'
                }, status=400)
            elif existing_invitation.status == 'ACCEPTED':
                return JsonResponse({
                    'status': 'error',
                    'message': 'This free agent has already joined a team'
                }, status=400)
        
        try:
            # Create invitation
            invitation = TeamInvitation.objects.create(
                free_agent=free_agent,
                team=team
            )
            
            # Update free agent status
            free_agent.status = 'INVITED'
            free_agent.save()
            
            messages.success(request, f'Invitation sent to {free_agent.first_name} {free_agent.last_name}')
            return JsonResponse({
                'status': 'success',
                'message': 'Invitation sent successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

class SentInvitationsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'invitations/sent_invitations.html'
    context_object_name = 'invitations'
    
    def test_func(self):
        return self.request.user.is_team_captain()
    
    def get_queryset(self):
        # Get all teams where user is captain
        captained_teams = Team.objects.filter(captain__user=self.request.user)
        
        # Get all invitations for these teams
        return TeamInvitation.objects.filter(
            team__in=captained_teams
        ).select_related(
            'team',
            'team__league',
            'team__division',
            'free_agent'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Get captained teams for the "View Free Agents" link
            captained_teams = Team.objects.filter(
                captain__user=self.request.user
            ).select_related('league')
            
            # Group invitations by status
            grouped_invitations = {
                'PENDING': [],
                'ACCEPTED': [],
                'DECLINED': [],
                'EXPIRED': []
            }
            
            for invitation in self.get_queryset():
                # Check if invitation has expired
                if invitation.status == 'PENDING' and self._is_invitation_expired(invitation):
                    invitation.status = 'EXPIRED'
                    invitation.save()
                    grouped_invitations['EXPIRED'].append(invitation)
                else:
                    grouped_invitations[invitation.status].append(invitation)
                    
            context.update({
                'grouped_invitations': grouped_invitations,
                'captained_teams': captained_teams,
                'invitation_form': TeamInvitationForm()
            })
            
        except Exception as e:
            logger.error(f"Error in SentInvitationsView get_context_data: {str(e)}")
            messages.error(
                self.request, 
                "An error occurred while loading invitations. Please try again."
            )
            context.update({
                'grouped_invitations': {
                    'PENDING': [],
                    'ACCEPTED': [],
                    'DECLINED': [],
                    'EXPIRED': []
                },
                'captained_teams': [],
                'invitation_form': TeamInvitationForm()
            })
            
        return context
    
    def _is_invitation_expired(self, invitation):
        """Check if an invitation has expired (older than 7 days)"""
        if not invitation.created_at:
            return False
        
        expiration_days = 7  # You could make this configurable
        expiration_date = invitation.created_at + timezone.timedelta(days=expiration_days)
        return timezone.now() > expiration_date

class AcceptInvitationView(LoginRequiredMixin, View):
    def post(self, request, invitation_id):
        api_client = ApiClient(request)
        
        try:
            # Accept invitation through API
            response = api_client.post(f'invitations/{invitation_id}/accept/')
            messages.success(request, response['message'])
            
        except Exception as e:
            logger.error(f"API call failed in AcceptInvitationView: {str(e)}")
            messages.error(request, "Unable to accept invitation at this time")
            
        return redirect('players:my_free_agent_registrations')

class DeclineInvitationView(LoginRequiredMixin, View):
    def post(self, request, invitation_id):
        api_client = ApiClient(request)
        
        try:
            # Decline invitation through API
            response = api_client.post(f'invitations/{invitation_id}/decline/')
            messages.success(request, response['message'])
            
        except Exception as e:
            logger.error(f"API call failed in DeclineInvitationView: {str(e)}")
            messages.error(request, "Unable to decline invitation at this time")
            
        return redirect('players:my_free_agent_registrations')

class CancelInvitationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_team_captain()
        
    def post(self, request, invitation_id):
        api_client = ApiClient(request)
        
        try:
            # Cancel invitation through API
            response = api_client.post(f'invitations/{invitation_id}/cancel/')
            return JsonResponse({'status': 'success', 'message': response['message']})
            
        except Exception as e:
            logger.error(f"API call failed in CancelInvitationView: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': "Unable to cancel invitation at this time"
            }, status=500)
    def test_func(self):
        invitation = get_object_or_404(TeamInvitation, id=self.kwargs['invitation_id'])
        return self.request.user == invitation.team.captain.user
        
    def post(self, request, invitation_id):
        invitation = get_object_or_404(TeamInvitation, id=invitation_id)
        invitation.status = 'CANCELLED'
        invitation.save()
        return JsonResponse({'status': 'success'})
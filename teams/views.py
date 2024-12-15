from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, TemplateView
from django.http import JsonResponse

from .models import Team, TeamCaptain
from .forms import TeamEditForm, TeamSignupForm
from players.models import Player
from leagues.models import League, Division
from api.client import ApiClient

class TeamDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'teams/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = ApiClient(self.request)
        
        try:
            # Get teams where user is captain
            captained_teams = api_client.get('teams/captained/')
            
            # Get teams that can be claimed
            potential_teams = api_client.get('teams/claimable/')
            
            context.update({
                'teams_as_captain': captained_teams,
                'potential_captain_teams': potential_teams,
            })
            
        except Exception as e:
            logger.error(f"API call failed in TeamDashboardView: {str(e)}")
            # Fallback to direct database queries
            teams_as_captain = Team.objects.filter(captain__user=self.request.user)
            potential_captain_teams = Team.objects.filter(
                captain__email=self.request.user.email,
                captain__user__isnull=True
            )
            
            context.update({
                'teams_as_captain': teams_as_captain,
                'potential_captain_teams': potential_captain_teams,
            })
            
        return context

class TeamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'
    
    def test_func(self):
        team = self.get_object()
        return (team.captain.user == self.request.user or 
                (team.captain.email == self.request.user.email and team.captain.user is None))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        api_client = ApiClient(self.request)

        try:
            # Get team players from API
            team_players = api_client.get(f'teams/{team.id}/players/')
            
            # If captain, get pending invitations
            if self.test_func():
                pending_invitations = api_client.get(f'teams/{team.id}/pending-invitations/')
            else:
                pending_invitations = None

            context.update({
                'is_captain': self.test_func(),
                'league': team.league,
                'players': team_players,
                'pending_invitations': pending_invitations,
            })
        except Exception as e:
            # Log error and fall back to direct database query
            logger.error(f"API call failed in TeamDetailView: {str(e)}")
            context.update({
                'is_captain': self.test_func(),
                'league': team.league,
                'players': team.players.all(),
                'pending_invitations': team.sent_invitations.filter(status='PENDING') if self.test_func() else None,
            })

        return context
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'
    
    def test_func(self):
        team = self.get_object()
        return (team.captain.user == self.request.user or 
                (team.captain.email == self.request.user.email and team.captain.user is None))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        is_captain = (team.captain.user == self.request.user or 
                     (team.captain.email == self.request.user.email and team.captain.user is None))
            
        context.update({
            'is_captain': is_captain,
            'league': team.league,
            'pending_invitations': None,  # This will be updated when we move invitations
        })
        return context

class TeamManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teams/team_management.html'

    def test_func(self):
        return self.request.user.is_admin()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = ApiClient(self.request)

        try:
            # Get filter parameters
            league_id = self.request.GET.get('league')
            division_id = self.request.GET.get('division')
            search_query = self.request.GET.get('search', '')

            # Build API parameters
            params = {}
            if league_id:
                params['league'] = league_id
            if division_id:
                params['division'] = division_id
            if search_query:
                params['search'] = search_query

            # Get teams with filters
            teams = api_client.get('teams/manage/', params=params)
            
            # Get leagues and divisions for filters
            leagues = api_client.get('leagues/all/')
            divisions = api_client.get('divisions/all/')

            context.update({
                'teams': teams,
                'leagues': leagues,
                'divisions': divisions,
                'selected_league': league_id,
                'selected_division': division_id,
                'search_query': search_query,
            })

        except Exception as e:
            logger.error(f"API call failed in TeamManagementView: {str(e)}")
            # Fallback to direct database queries
            queryset = Team.objects.select_related(
                'league',
                'division'
            ).order_by('league', 'division', 'name')
            
            # Apply filters
            filters = {}
            if league_id:
                filters['league_id'] = league_id
            if division_id:
                filters['division_id'] = division_id
            if search_query:
                filters['name__icontains'] = search_query
                
            teams = queryset.filter(**filters)
            
            context.update({
                'teams': teams,
                'leagues': League.objects.all().order_by('name'),
                'divisions': Division.objects.all().order_by('name'),
                'selected_league': league_id,
                'selected_division': division_id,
                'search_query': search_query,
            })

        return context

class TeamEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Team
    form_class = TeamEditForm
    template_name = 'teams/team_edit.html'
    
    def test_func(self):
        return self.request.user.is_admin()
    
    def get_success_url(self):
        messages.success(self.request, f"Team '{self.object.name}' was updated successfully.")
        return reverse_lazy('teams:team_management')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Team: {self.object.name}"
        return context

class ClaimTeamCaptainView(LoginRequiredMixin, View):
    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        
        # Check if this user's email matches the captain's email
        if team.captain.email == request.user.email and team.captain.user is None:
            team.captain.user = request.user
            team.captain.save()
            messages.success(request, "You have successfully claimed this team.")
        else:
            messages.error(request, "You are not authorized to claim this team.")
            
        return redirect('teams:team_dashboard')

class RemovePlayerView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        team = Team.objects.get(players=self.kwargs['player_id'])
        return self.request.user == team.captain.user
        
    def post(self, request, player_id):
        api_client = ApiClient(request)
        
        try:
            # Use API to remove player
            api_client.post(f'players/{player_id}/remove-from-team/')
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"API call failed in RemovePlayerView: {str(e)}")
            # Fallback to direct database operation
            try:
                player = get_object_or_404(Player, id=player_id)
                team = Team.objects.get(players=player)
                team.players.remove(player)
                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
            

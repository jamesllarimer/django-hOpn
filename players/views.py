from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, FormView, TemplateView, View
from django.utils import timezone
from datetime import datetime
from collections import defaultdict

from .models import FreeAgent
from registrations.models import Registration
from players.forms import FreeAgentRegistrationForm
from players.models import Player
from leagues.models import League, Division
from api.client import ApiClient

class FreeAgentRegistrationView(LoginRequiredMixin, FormView):
    template_name = 'players/free_agent_registration.html'
    form_class = FreeAgentRegistrationForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.league = get_object_or_404(League, id=self.kwargs['league_id'])
        kwargs['league'] = self.league
        return kwargs

    def form_valid(self, form):
        # Create the free agent profile
        free_agent = form.save(commit=False)
        free_agent.user = self.request.user
        free_agent.league = self.league
        free_agent.save()
        
        messages.success(self.request, "You have been successfully registered as a free agent!")
        return redirect('players:free_agent_registration_success')

class FreeAgentRegistrationSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'players/free_agent_registration_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class FreeAgentPoolView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'players/free_agent_pool.html'
    context_object_name = 'free_agents'
    
    def test_func(self):
        return self.request.user.is_team_captain()
    
    def get_queryset(self):
        league_id = self.kwargs.get('league_id')
        api_client = ApiClient(self.request)
        
        try:
            # Get free agents from API
            params = {}
            if self.request.GET.get('division'):
                params['division'] = self.request.GET['division']
                
            free_agents = api_client.get(
                f'free-agents/league/{league_id}/',
                params=params
            )
            return free_agents
        except Exception as e:
            # Log error and return empty list
            logger.error(f"API call failed in FreeAgentPoolView: {str(e)}")
            return []
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        league_id = self.kwargs.get('league_id')
        api_client = ApiClient(self.request)
        
        try:
            # Get divisions from API
            divisions = api_client.get(f'leagues/{league_id}/divisions/')
            league = get_object_or_404(League, id=league_id)
            
            context.update({
                'league': league,
                'divisions': divisions,
            })
        except Exception as e:
            # Log error and fall back to direct database query
            logger.error(f"API call failed in FreeAgentPoolView context: {str(e)}")
            league = get_object_or_404(League, id=league_id)
            context.update({
                'league': league,
                'divisions': league.available_divisions.all(),
            })
            
        return context
class FreeAgentDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'team') and self.request.user.team.is_captain(self.request.user)
        
    def get(self, request, agent_id):
        agent = get_object_or_404(FreeAgent, id=agent_id)
        data = {
            'id': agent.id,
            'first_name': agent.first_name,
            'last_name': agent.last_name,
            'division': agent.division.name,
            'date_of_birth': agent.date_of_birth.strftime('%B %d, %Y'),
            'is_member': agent.is_member,
            'notes': agent.notes
        }
        return JsonResponse(data)

class MyFreeAgentRegistrationsView(LoginRequiredMixin, ListView):
    template_name = 'players/my_free_agent_registrations.html'
    context_object_name = 'registrations'
    
    def get_queryset(self):
        return FreeAgent.objects.filter(
            user=self.request.user
        ).select_related(
            'league',
            'division'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registrations = self.get_queryset()
        
        # Group registrations by league
        leagues_data = defaultdict(list)
        for registration in registrations:
            leagues_data[registration.league].append(registration)
            
        context['leagues_data'] = dict(leagues_data)
        
        return context
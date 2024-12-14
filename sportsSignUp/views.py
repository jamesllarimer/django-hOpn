import datetime
import json
import logging
from urllib import request
from django import forms
from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.views.generic.edit import UpdateView
from django.views.generic import ListView, CreateView, FormView, DetailView, TemplateView
from datetime import datetime 
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView

from sportsSignUp.stripe_utils import get_stripe_price_id
from .forms import CustomUserCreationForm, FreeAgentRegistrationForm, ProfileUpdateForm, TeamSignupForm
from django.contrib import messages
from django.utils import timezone
from .models import CustomUser, Sport, Team, Player, Division, League, Registration, FreeAgent, TeamInvitation, TeamInvitationNotification
import stripe
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q
from collections import defaultdict
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.validators import validate_email
logger = logging.getLogger(__name__)
stripe.api_key = settings.TEST_STRIPE_SECRET_KEY


def index(request):
    teams_list = Team.objects.all()
    context = {
        "teams": teams_list,
    }
    return render(request, "index.html", context)
def get_teams_by_league(request, league_id):
        """API endpoint to get all teams organized by division for a league"""
        league = get_object_or_404(League, id=league_id)
        divisions = league.available_divisions.all()
    
        data = []
        for division in divisions:
            teams = Team.objects.filter(
                league=league,
                division=division
            ).values('id', 'name')
        
            data.append({
                'id': division.id,
                'name': division.name,
                'teams': list(teams)
            })
    
        return JsonResponse(data, safe=False)

@require_POST
def assign_team(request, player_id):
    """Handle team assignment for a player"""
    print("Received POST data:", request.POST)  # Debug print
    print("team_id from POST:", request.POST.get('team_id'))  # Debug print
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin privileges required'}, status=403)

    try:
        team_id = request.POST.get('team_id')
        if not team_id:
            return JsonResponse({'error': 'No team_id provided in form data'}, status=400)

        print(f"Looking up team with ID: {team_id}")  # Debug print
        team = get_object_or_404(Team, id=team_id)
        player = get_object_or_404(Player, id=player_id)
        
        # Get the player's registration for this league
        registration = Registration.objects.filter(
            player=player,
            league=team.league
        ).first()
        
        if registration:
            # Store old values for messaging
            old_division = registration.division
            old_team = player.team
            
            # Update registration with new division
            registration.division = team.division
            registration.save()
            
            # Update player's team
            player.team = team
            player.save()
            
            # Prepare message about changes
            changes = []
            if old_team != team:
                changes.append(f"Team changed from {old_team.name if old_team else 'Free Agent'} to {team.name}")
            if old_division != team.division:
                changes.append(f"Division changed from {old_division.name} to {team.division.name}")
            
            message = " and ".join(changes)
        else:
            return JsonResponse({
                'error': f"No registration found for player {player.get_full_name()} in league {team.league.name}"
            }, status=400)
        
        return JsonResponse({
            'status': 'success',
            'message': message
        })
        
    except Exception as e:
        print(f"Error in assign_team: {str(e)}")  # Debug print
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=400)
    
def active_leagues(request):
    """
    View to display currently active leagues
    A league is considered active if:
    1. Registration has started
    2. Registration has not ended
    """
    # Get current date
    today = timezone.now().date()

    # Filter for active leagues
    active_leagues = League.objects.filter(
        registration_start_date__lte=today,  # Registration has started
        registration_end_date__gte=today     # Registration has not ended
    ).order_by('registration_end_date')

    context = {
        'active_leagues': active_leagues,
        'page_title': 'Active Leagues'
    }

    return render(request, 'active_leagues.html', context)
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in after registration
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        login(self.request, user)
        messages.success(self.request, 'Account created successfully!')
        return response
class ProfileManagementView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'registration/profile_management.html'
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_of_birth']
    success_url = reverse_lazy('profile_management')

    def get_object(self, queryset=None):
        return self.request.user    

class ProfileManagementView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'registration/profile_management.html'
    success_url = reverse_lazy('sportsSignUp:profile_management')

    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)
    
class LeagueListView(ListView):
    template_name = 'leagues/league_list.html'
    context_object_name = 'sports'
    
    def get_queryset(self):
        # Get current date
        today = timezone.now().date()
        
        # Get all sports and their active leagues
        sports = Sport.objects.prefetch_related('leagues').all()
        
        # Filter for active leagues
        for sport in sports:
            sport.active_leagues = sport.leagues.filter(
                registration_start_date__lte=today,
                registration_end_date__gte=today
            ).select_related('sport').prefetch_related('available_divisions')
            
        return sports

class FreeAgentRegistrationSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'leagues/free_agent_registration_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class FreeAgentRegistrationView(LoginRequiredMixin, FormView):
    template_name = 'leagues/free_agent_registration.html'
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
        return redirect('sportsSignUp:free_agent_registration_success')
    
class MyFreeAgentRegistrationsView(LoginRequiredMixin, ListView):
    template_name = 'leagues/my_free_agent_registrations.html'
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
        
        # Get all received invitations
        context['pending_invitations'] = TeamInvitation.objects.filter(
            free_agent__user=self.request.user,
            status='PENDING'
        ).select_related(
            'team',
            'team__league',
            'team__division',
            'team__captain'
        )

        context['all_invitations'] = TeamInvitation.objects.filter(
            free_agent__user=self.request.user
        ).select_related(
            'team',
            'team__league',
            'team__division',
            'team__captain'
        ).order_by('-created_at')
        
        return context
class DeclineInvitationView(LoginRequiredMixin, View):
    def post(self, request, invitation_id):
        try:
            # Get invitation and verify ownership
            invitation = get_object_or_404(TeamInvitation, 
                id=invitation_id,
                free_agent__user=request.user,
                status='PENDING'
            )
            
            # Update invitation status
            invitation.status = 'DECLINED'
            invitation.response_at = timezone.now()
            invitation.save()
            
            # Update free agent status back to available
            invitation.free_agent.status = 'AVAILABLE'
            invitation.free_agent.save()
            
            messages.success(request, f"You have declined the invitation from {invitation.team.name}.")
            
        except TeamInvitation.DoesNotExist:
            messages.error(request, "Invitation not found or already processed.")
        except Exception as e:
            messages.error(request, f"Error processing invitation: {str(e)}")
        
        return redirect('sportsSignUp:my_free_agent_registrations')    
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
        
        # Use the first team if there are multiple (you might want to handle this differently)
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
    template_name = 'teams/sent_invitations.html'
    context_object_name = 'invitations'
    
    def test_func(self):
        return self.request.user.is_team_captain()
    
    def get_queryset(self):
        # Get all teams where user is captain
        captained_teams = Team.objects.filter(
            captain__user=self.request.user
        )
        
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
        # Get captained teams
        captained_teams = Team.objects.filter(
            captain__user=self.request.user
        ).select_related('league')
        
        context['captained_teams'] = captained_teams
        
        # Group invitations by status
        grouped_invitations = {
            'PENDING': [],
            'ACCEPTED': [],
            'DECLINED': [],
            'EXPIRED': []
        }
        
        for invitation in self.get_queryset():
            grouped_invitations[invitation.status].append(invitation)
            
        context['grouped_invitations'] = grouped_invitations
        return context
    
class RemovePlayerView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        team = Team.objects.get(players=self.kwargs['player_id'])
        return self.request.user == team.captain
        
    def post(self, request, player_id):
        player = get_object_or_404(CustomUser, id=player_id)
        team = Team.objects.get(players=player)
        team.players.remove(player)
        return JsonResponse({'status': 'success'})

class CancelInvitationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        invitation = get_object_or_404(TeamInvitation, id=self.kwargs['invitation_id'])
        return self.request.user == invitation.team.captain
        
    def post(self, request, invitation_id):
        invitation = get_object_or_404(TeamInvitation, id=invitation_id)
        invitation.status = 'CANCELLED'
        invitation.save()
        return JsonResponse({'status': 'success'})
class AcceptInvitationView(LoginRequiredMixin, View):
    def post(self, request, invitation_id):
        try:
            # Get invitation and verify ownership
            invitation = get_object_or_404(TeamInvitation, 
                id=invitation_id,
                free_agent__user=request.user
            )
            
            # Check if the league registration is still open
            if invitation.team.league.registration_end_date < timezone.now().date():
                messages.error(request, "League registration has ended. You can no longer accept this invitation.")
                return redirect('sportsSignUp:my_free_agent_registrations')
            
            # Check if the team is full (you might want to add a max_players field to Team model)
            if hasattr(invitation.team, 'max_players') and invitation.team.players.count() >= invitation.team.max_players:
                messages.error(request, "This team is now full and cannot accept new players.")
                return redirect('sportsSignUp:my_free_agent_registrations')
            
            # Update invitation status
            invitation.status = 'ACCEPTED'
            invitation.response_at = timezone.now()
            invitation.save()
            
            # Update free agent status
            invitation.free_agent.status = 'JOINED'
            invitation.free_agent.save()
            
            # Create or update player record
            player, created = Player.objects.get_or_create(
                user=request.user,
                team=invitation.team,
                defaults={
                    'first_name': invitation.free_agent.first_name,
                    'last_name': invitation.free_agent.last_name,
                    'email': invitation.free_agent.email,
                    'phone_number': invitation.free_agent.phone_number,
                    'date_of_birth': invitation.free_agent.date_of_birth,
                    'is_active': True
                }
            )
            
            # Create registration record
            Registration.objects.get_or_create(
                player=player,
                league=invitation.team.league,
                division=invitation.team.division,
                defaults={
                    'payment_status': 'pending',
                    'is_late_registration': timezone.now().date() > invitation.team.league.early_registration_deadline
                }
            )
            
            messages.success(request, f"You have successfully joined {invitation.team.name}!")
            
            # Decline all other pending invitations
            TeamInvitation.objects.filter(
                free_agent__user=request.user,
                status='PENDING'
            ).exclude(
                id=invitation_id
            ).update(
                status='DECLINED',
                response_at=timezone.now()
            )
            
        except TeamInvitation.DoesNotExist:
            messages.error(request, "Invitation not found.")
        except Exception as e:
            messages.error(request, f"Error processing invitation: {str(e)}")
        
        return redirect('sportsSignUp:my_free_agent_registrations')
        
class FreeAgentPoolView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = FreeAgent
    template_name = 'leagues/free_agent_pool.html'
    context_object_name = 'free_agents'
    
    def test_func(self):
        return self.request.user.is_team_captain()
    
    def get_queryset(self):
        # Get the league from the URL
        league_id = self.kwargs.get('league_id')
        
        # Filter free agents by league and available status
        queryset = FreeAgent.objects.filter(
            league_id=league_id,
            status='AVAILABLE'
        ).order_by('-created_at')
        
        # Apply filters from query parameters
        division = self.request.GET.get('division')
        if division:
            queryset = queryset.filter(division_id=division)
            
        age_group = self.request.GET.get('age_group')
        if age_group:
            # You might want to implement age group logic based on date_of_birth
            pass
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        league = get_object_or_404(League, id=self.kwargs.get('league_id'))
        context['league'] = league
        context['divisions'] = league.available_divisions.all()
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
class TeamDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'teams/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teams where user is captain (through TeamCaptain)
        teams_as_captain = Team.objects.filter(captain__user=user)
        
        # In your case, you might want to also get teams where the user's email
        # matches a TeamCaptain email but hasn't been linked yet
        potential_captain_teams = Team.objects.filter(
            captain__email=user.email,
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
        is_captain = (team.captain.user == self.request.user or 
                     (team.captain.email == self.request.user.email and team.captain.user is None))
            
        context.update({
            'is_captain': is_captain,
            'league': team.league,
            'pending_invitations': TeamInvitation.objects.filter(
                team=team, 
                status='PENDING'
            ) if is_captain else None,
        })
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
            
        return redirect('sportsSignUp:team_dashboard')
def registration_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'No session ID provided')
        return redirect('sportsSignUp:league_list')

    try:
        # Retrieve the Stripe session
        session = stripe.checkout.Session.retrieve(session_id)
        player_data = json.loads(session.metadata['player_data'])
        
        # Create or get the Player
        player = Player.objects.create(
            first_name=player_data['first_name'],
            last_name=player_data['last_name'],
            email=player_data['email'],
            phone_number=player_data['phone_number'],
            parent_name=player_data.get('parent_name'),
            date_of_birth=datetime.strptime(player_data['date_of_birth'], '%Y-%m-%d').date(),
            membership_number=player_data['membership_number'],
            is_member=player_data['is_member'],
            user=request.user if request.user.is_authenticated else None
        )
        
        # Create the Registration
        registration = Registration.objects.create(
            player=player,
            league_id=session.metadata['league_id'],
            payment_status='paid',
            stripe_payment_intent=session.payment_intent,
            stripe_checkout_session=session_id,  # You might want to add this field to your model
            notes=player_data.get('notes', ''),
            is_late_registration=session.metadata.get('is_late_registration', 'false') == 'true',
            division_id=session.metadata['division_id']
        )

        messages.success(request, 'Registration completed successfully!')
        return redirect('sportsSignUp:league_list')
        
    except Exception as e:
        messages.error(request, f'Error processing registration: {str(e)}')
        return redirect('sportsSignUp:league_list')
    
def registration_cancel(request, league_id):
    messages.error(request, 'Registration canceled')
    return redirect('sportsSignUp:league_list')
from django.views.generic import ListView
from .mixins import AdminRequiredMixin

class RegistrationManagementView(AdminRequiredMixin, ListView):
    template_name = 'registration/registration_management.html'
    model = Registration
    context_object_name = 'registrations'

    def get_queryset(self):
        queryset = Registration.objects.select_related(
            'player',
            'league',
            'division',
            'player__team'
        ).order_by('division', 'player__team', 'player__last_name')
        
        # Apply filters
        filters = Q()
        
        # League filter
        league_id = self.request.GET.get('league')
        if league_id:
            filters &= Q(league_id=league_id)
            
        # Division filter
        division_id = self.request.GET.get('division')
        if division_id:
            filters &= Q(division_id=division_id)
            
        # Team filter
        team_id = self.request.GET.get('team')
        if team_id:
            filters &= Q(player__team_id=team_id)
            
        # Search filter
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            search_filters = (
                Q(player__first_name__icontains=search_query) |
                Q(player__last_name__icontains=search_query) |
                Q(player__email__icontains=search_query) |
                Q(player__phone_number__icontains=search_query)
            )
            filters &= search_filters
            
        return queryset.filter(filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current filter values
        league_id = self.request.GET.get('league')
        division_id = self.request.GET.get('division')
        team_id = self.request.GET.get('team')
        search_query = self.request.GET.get('search', '')
        
        # Get all leagues for the filter
        context['leagues'] = League.objects.all().order_by('name')
        context['selected_league'] = league_id
        
        # Get divisions based on selected league
        if league_id:
            context['divisions'] = Division.objects.filter(
                league_sessions__id=league_id
            ).distinct().order_by('name')
        else:
            context['divisions'] = Division.objects.none()
        context['selected_division'] = division_id
        
        # Get teams based on selected division
        if division_id:
            context['teams'] = Team.objects.filter(
                division_id=division_id
            ).order_by('name')
        else:
            context['teams'] = Team.objects.none()
        context['selected_team'] = team_id
        
        # Keep the search query
        context['search_query'] = search_query
        
        # Organize registrations
        organized_data = defaultdict(lambda: defaultdict(list))
        free_agents = defaultdict(list)
        
        for registration in self.get_queryset():
            if registration.player.team:
                organized_data[registration.division][registration.player.team].append(registration)
            else:
                free_agents[registration.division].append(registration)

        # Convert to regular dicts
        context['organized_data'] = {
            division: dict(teams_dict)
            for division, teams_dict in organized_data.items()
        }
        context['free_agents'] = dict(free_agents)
        
        # Stats for current filter
        current_queryset = self.get_queryset()
        context['stats'] = {
            'total_registrations': current_queryset.count(),
            'total_free_agents': current_queryset.filter(player__team__isnull=True).count(),
            'divisions_count': current_queryset.values('division').distinct().count(),
            'teams_count': current_queryset.exclude(player__team__isnull=True)
                .values('player__team').distinct().count(),
        }
        
        return context
    

def get_registrations_by_league(request, league_id):
    """
    Retrieve registrations for a specific league with error handling and validation.
    Includes team information through the Player model relationship.
    """
    try:
        # Validate league_id
        if not isinstance(league_id, int) and not str(league_id).isdigit():
            logger.error(f"Invalid league_id format: {league_id}")
            return JsonResponse({
                'error': 'Invalid league ID format'
            }, status=400)

        # Verify league exists
        league = get_object_or_404(League, id=league_id)
        
        try:
            # Updated query to include player and their team information
            registrations = Registration.objects.filter(
                league_id=league_id
            ).select_related(
                'division',
                'player',
                'player__team'  # Include team data through player
            ).values(
                # Registration fields
                'id',
                'division_id',
                'division__name',
                'is_late_registration',
                'payment_status',
                'registered_at',
                'notes',
                # Player fields
                'player__id',
                'player__first_name',
                'player__last_name',
                'player__parent_name',
                'player__email',
                'player__phone_number',
                'player__is_member',
                # Team fields (through player)
                'player__team__id',
                'player__team__name',
                'player__team__division__id',
                'player__team__division__name'
            )

            data = []
            for reg in registrations:
                try:
                    # Basic validation of required fields
                    if not reg['player__first_name'] or not reg['player__email']:
                        logger.warning(f"Registration {reg['id']} has missing required fields")
                        continue

                    # Validate email format
                    validate_email(reg['player__email'])

                    # Combine first and last name
                    full_name = f"{reg['player__first_name']} {reg['player__last_name']}".strip()

                    # Transform the registration data
                    registration_data = {
                        'id': reg['id'],
                        'player_id': reg['player__id'],
                        'player_name': full_name,
                        'parent_name': reg['player__parent_name'].strip() if reg['player__parent_name'] else None,
                        'email': reg['player__email'].lower(),
                        'phone': reg['player__phone_number'],
                        'division_id': reg['division_id'],
                        'division_name': reg['division__name'],
                        # Team information (null if free agent)
                        'team_id': reg['player__team__id'],
                        'team_name': reg['player__team__name'],
                        'team_division_id': reg['player__team__division__id'],
                        'team_division_name': reg['player__team__division__name'],
                        # Status information
                        'is_late_registration': reg['is_late_registration'],
                        'payment_status': reg['payment_status'],
                        'is_member': reg['player__is_member'],
                        'registered_at': reg['registered_at'].isoformat() if reg['registered_at'] else None,
                        'notes': reg['notes']
                    }

                    data.append(registration_data)

                except forms.ValidationError as ve:
                    logger.error(f"Validation error for registration {reg['id']}: {str(ve)}")
                    continue
                except KeyError as ke:
                    logger.error(f"Missing key in registration data: {str(ke)}")
                    continue

            # Log success
            logger.info(f"Successfully retrieved {len(data)} registrations for league {league_id}")

            return JsonResponse(data, safe=False)

        except Exception as e:
            logger.error(f"Database error while fetching registrations: {str(e)}")
            return JsonResponse({
                'error': 'Error retrieving registrations'
            }, status=500)

    except League.DoesNotExist:
        logger.error(f"League {league_id} not found")
        return JsonResponse({
            'error': 'League not found'
        }, status=404)

    except Exception as e:
        logger.error(f"Unexpected error in get_registrations_by_league: {str(e)}")
        return JsonResponse({
            'error': 'An unexpected error occurred'
        }, status=500)
    
def get_divisions_by_league(request, league_id):
    divisions = Division.objects.filter(
        league_sessions__id=league_id
    ).distinct().values('id', 'name')
    return JsonResponse(list(divisions), safe=False)

def divisions_and_teams_by_league(request, league_id):
    # Get divisions through league sessions
    divisions = Division.objects.filter(
        league_sessions__id=league_id
    ).distinct().prefetch_related('teams')
    
    data = [{
        'id': division.id,
        'name': division.name,
        'teams': [{
            'id': team.id,
            'name': team.name
        } for team in division.teams.all()]
    } for division in divisions]
    
    return JsonResponse(data, safe=False)
def get_teams_by_division(request, division_id):
    teams = Team.objects.filter(
        division_id=division_id
    ).values('id', 'name')
    return JsonResponse(list(teams), safe=False)

class TeamManagementView(AdminRequiredMixin, ListView):
    model = Team
    template_name = 'teams/team_management.html'  # This tells ListView to use this template
    context_object_name = 'teams'

    def get_queryset(self):
        queryset = Team.objects.select_related(
            'league',
            'division'
        ).order_by('league', 'division', 'name')
        
        # Apply filters
        filters = Q()
        
        # League filter
        league_id = self.request.GET.get('league')
        if league_id:
            filters &= Q(league_id=league_id)
            
        # Division filter
        division_id = self.request.GET.get('division')
        if division_id:
            filters &= Q(division_id=division_id)
            
        # Search filter
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            filters &= Q(name__icontains=search_query)
            
        return queryset.filter(filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['leagues'] = League.objects.all().order_by('name')
        context['divisions'] = Division.objects.all().order_by('name')
        return context

class TeamEditForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'division', 'league']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'division': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'league': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If instance exists (editing existing team), get its current league
        if self.instance.pk:
            self.fields['division'].queryset = Division.objects.filter(
                league_sessions=self.instance.league
            )

    def clean(self):
        cleaned_data = super().clean()
        division = cleaned_data.get('division')
        league = cleaned_data.get('league')
        
        if division and league:
            # Verify division belongs to the selected league
            if league not in division.league_sessions.all():
                raise forms.ValidationError(
                    "Selected division is not available in the selected league."
                )
        return cleaned_data

class TeamEditView(AdminRequiredMixin, UpdateView):
    model = Team
    form_class = TeamEditForm
    template_name = 'teams/team_edit.html'
    
    def get_success_url(self):
        messages.success(self.request, f"Team '{self.object.name}' was updated successfully.")
        return reverse('sportsSignUp:team_management')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Team: {self.object.name}"
        return context

def team_signup_page(request, signup_code):
    """Public page for team signups"""
    team = get_object_or_404(Team, signup_code=signup_code)

    if request.method == 'POST':
        form = TeamSignupForm(request.POST)
        if form.is_valid():
            try:
                # Get the appropriate price ID
                price_id = get_stripe_price_id(
                    league=team.league,
                    is_member=form.cleaned_data['is_member'],
                )
                
                if not price_id:
                    messages.error(request, "Unable to determine registration price. Please contact support.")
                    return redirect('sportsSignUp:team_signup', signup_code=signup_code)

                # Create Stripe checkout session
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price': price_id,
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=request.build_absolute_uri(
                        reverse('sportsSignUp:team_signup_success')
                    ) + "?session_id={CHECKOUT_SESSION_ID}",
                    cancel_url=request.build_absolute_uri(
                        reverse('sportsSignUp:team_signup', kwargs={'signup_code': signup_code})
                    ),
                    metadata={
                        'team_id': team.id,
                        'player_data': json.dumps({
                            'first_name': form.cleaned_data['first_name'],
                            'last_name': form.cleaned_data['last_name'],
                            'email': form.cleaned_data['email'],
                            'phone_number': form.cleaned_data['phone_number'],
                            'parent_name': form.cleaned_data.get('parent_name', ''),
                            'date_of_birth': str(form.cleaned_data['date_of_birth']),
                            'membership_number': form.cleaned_data['membership_number'],
                            'is_member': form.cleaned_data['is_member'],
                        })
                    }
                )
                return redirect(checkout_session.url)
                
            except stripe.error.StripeError as e:
                messages.error(request, f"Payment error: {str(e)}")
                return redirect('team_signup', signup_code=signup_code)
    else:
        form = TeamSignupForm()

    return render(request, 'teams/team_signup.html', {
        'team': team,
        'form': form,
    })

def team_signup_success(request):
    """Handle successful team signup after payment"""
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'No session ID provided')
        return redirect('')

    try:
        # Retrieve the session and metadata
        session = stripe.checkout.Session.retrieve(session_id)
        player_data = json.loads(session.metadata['player_data'])
        team = get_object_or_404(Team, id=session.metadata['team_id'])
        
        # Create the player
        player = Player.objects.create(
            first_name=player_data['first_name'],
            last_name=player_data['last_name'],
            email=player_data['email'],
            phone_number=player_data['phone_number'],
            parent_name=player_data.get('parent_name'),
            date_of_birth=datetime.strptime(player_data['date_of_birth'], '%Y-%m-%d').date(),
            membership_number=player_data['membership_number'],
            is_member=player_data['is_member'],
            team=team
        )
        
        # Create registration
        registration = Registration.objects.create(
            player=player,
            league=team.league,
            division=team.division,
            payment_status='paid',
            stripe_payment_intent=session.payment_intent
        )
        
        messages.success(request, 'Registration completed successfully!')
        return redirect('sportsSignUp:teams/team_signup_success')
        
    except Exception as e:
        messages.error(request, f'Error processing registration: {str(e)}')
        return redirect('/')

def send_team_email(request, team_id):
    """Send email to all team members"""
    if not request.user.is_admin():
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    team = get_object_or_404(Team, id=team_id)
    subject = request.POST.get('subject')
    message = request.POST.get('message')
    
    try:
        recipients = team.players.values_list('email', flat=True)
        # Add your email sending logic here
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
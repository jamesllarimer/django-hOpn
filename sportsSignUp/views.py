import datetime
import json
from urllib import request
from django import forms
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import ListView, CreateView, FormView
from datetime import datetime 
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView

from sportsSignUp.stripe_utils import get_stripe_price_id
from .forms import CustomUserCreationForm, FreeAgentRegistrationForm
from django.contrib import messages
from django.utils import timezone
from .models import Sport, Team, Player, Division, League, Registration
import stripe
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from collections import defaultdict
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages

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

class FreeAgentRegistrationView(LoginRequiredMixin, FormView):
    template_name = 'leagues/free_agent_registration.html'
    form_class = FreeAgentRegistrationForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.league = get_object_or_404(League, id=self.kwargs['league_id'])
        kwargs['league'] = self.league
        return kwargs

    def form_valid(self, form):
        league_id = self.kwargs['league_id']
        league = get_object_or_404(League, id=league_id)
        today = timezone.now().date()
        
        # Get the appropriate price ID
        price_id = 'price_1Nj6w4A4CECRU4aHIDEv90eE'
        line_items = [{
            'price': price_id,
            'quantity': 1,
        }]
        # If you have a fixed price ID for the late fee in Stripe
        is_late = True
        if is_late:
            line_items.append({
                'price': 'price_1QR3hBA4CECRU4aHgeNYJLTf',  # Your Stripe Price ID for the late fee
                'quantity': 1
        })
        if not price_id:
            messages.error(self.request, "Unable to find appropriate price. Please contact support.")
            return self.form_invalid(form)
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=self.request.build_absolute_uri(
                    reverse('sportsSignUp:registration_success')  
                ) + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=self.request.build_absolute_uri(
                    reverse('sportsSignUp:registration_cancel')  
                ),
                metadata={
                    'league_id': league_id,
                    'division_id': str(form.cleaned_data['division'].id),
                    'player_data': json.dumps({
                        'first_name': form.cleaned_data['first_name'],
                        'last_name': form.cleaned_data['last_name'],
                        'email': form.cleaned_data['email'],
                        'phone_number': form.cleaned_data['phone_number'],
                        'parent_name': form.cleaned_data.get('parent_name', ''),
                        'date_of_birth': str(form.cleaned_data['date_of_birth']),
                        'membership_number': form.cleaned_data['membership_number'],
                        'is_member': form.cleaned_data['is_member'],
                        'notes': form.cleaned_data.get('notes', ''),
                    })
                }
            )
            return redirect(checkout_session.url)
            
        except Exception as e:
            messages.error(self.request, f"Payment error: {str(e)}")
            return self.form_invalid(form)

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
        
        # Filter by league if specified
        league_id = self.request.GET.get('league')
        if league_id:
            queryset = queryset.filter(league_id=league_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all leagues for the filter
        context['leagues'] = League.objects.all().order_by('name')
        context['selected_league'] = self.request.GET.get('league')
        
        # Organize registrations by division and team
        organized_data = defaultdict(lambda: defaultdict(list))
        free_agents = defaultdict(list)
        
        print("\nDetailed Registration Analysis:")
        for registration in self.get_queryset():
            print(f"\nRegistration #{registration.id}")
            print(f"Player: {registration.player.get_full_name()}")
            print(f"League: {registration.league}")
            print(f"Division: {registration.division}")
            print(f"Player's Team: {registration.player.team}")
            print(f"Payment Status: {registration.payment_status}")

            # Validating data completeness
            if not registration.division:
                print("WARNING: Registration has no division")
                continue

            if registration.player.team:
                team = registration.player.team
                print(f"Team Division: {team.division}")
                print(f"Team League: {team.league}")
                
                # Check if team's division matches registration's division
                if team.division != registration.division:
                    print(f"WARNING: Team division ({team.division}) doesn't match registration division ({registration.division})")
                
                organized_data[registration.division][team].append(registration)
                print(f"Added to organized data under division '{registration.division}' and team '{team}'")
            else:
                free_agents[registration.division].append(registration)
                print("Added to free agents")

        # Print organized data structure
        print("\nOrganized Data Structure:")
        for division, teams in organized_data.items():
            print(f"\nDivision: {division.name}")
            for team, registrations in teams.items():
                print(f"  Team: {team.name}")
                print(f"  Players: {', '.join(r.player.get_full_name() for r in registrations)}")

        # Print free agents structure
        print("\nFree Agents Structure:")
        for division, registrations in free_agents.items():
            print(f"\nDivision: {division.name}")
            print(f"Players: {', '.join(r.player.get_full_name() for r in registrations)}")

        context['organized_data'] = dict(organized_data)
        context['free_agents'] = dict(free_agents)
        
        # Get some statistics
        stats_queryset = self.get_queryset()
        context['stats'] = {
            'total_registrations': stats_queryset.count(),
            'total_free_agents': stats_queryset.filter(player__team__isnull=True).count(),
            'divisions_count': stats_queryset.values('division').distinct().count(),
            'teams_count': stats_queryset.exclude(player__team__isnull=True)
                .values('player__team').distinct().count(),
        }
        
        return context


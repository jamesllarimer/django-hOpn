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

stripe.api_key = settings.TEST_STRIPE_SECRET_KEY


def index(request):
    teams_list = Team.objects.all()
    context = {
        "teams": teams_list,
    }
    return render(request, "index.html", context)

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
            'division'
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
        
        for registration in self.get_queryset():
            if registration.player.team:
                organized_data[registration.division][registration.player.team].append(registration)
            else:
                free_agents[registration.division].append(registration)
        
        context['organized_data'] = dict(organized_data)
        context['free_agents'] = dict(free_agents)
        
        # Get some statistics
        context['stats'] = {
            'total_registrations': self.get_queryset().count(),
            'total_free_agents': self.get_queryset().filter(player__team__isnull=True).count(),
            'divisions_count': self.get_queryset().values('division').distinct().count(),
            'teams_count': self.get_queryset().exclude(player__team__isnull=True)
                .values('player__team').distinct().count(),
        }
        
        return context
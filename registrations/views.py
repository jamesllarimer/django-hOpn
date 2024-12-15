import json
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, TemplateView
from django.utils import timezone
from datetime import datetime
from collections import defaultdict
from django.db.models import Q

from .models import Registration, StripeProduct, StripePrice
from players.models import Player
from leagues.models import League, Division

stripe.api_key = settings.TEST_STRIPE_SECRET_KEY

class RegistrationManagementView(UserPassesTestMixin, TemplateView):
    template_name = 'registrations/registration_management.html'

    def test_func(self):
        return self.request.user.is_admin()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = ApiClient(self.request)

        try:
            # Get current filter values
            league_id = self.request.GET.get('league')
            division_id = self.request.GET.get('division')
            search_query = self.request.GET.get('search', '')

            # Prepare API parameters
            params = {}
            if division_id:
                params['division'] = division_id
            if search_query:
                params['search'] = search_query

            if league_id:
                # Get registrations for specific league
                registrations = api_client.get(
                    f'leagues/{league_id}/registrations/',
                    params=params
                )
                # Get registration stats
                stats = api_client.get(f'leagues/{league_id}/registration-stats/')
                
                # Get divisions for this league
                divisions = api_client.get(f'leagues/{league_id}/divisions/')
            else:
                registrations = []
                stats = {
                    'total_registrations': 0,
                    'total_free_agents': 0,
                    'divisions_count': 0,
                    'teams_count': 0,
                }
                divisions = []

            context.update({
                'registrations': registrations,
                'stats': stats,
                'divisions': divisions,
                'leagues': League.objects.all().order_by('name'),  # This could also come from API
                'selected_league': league_id,
                'selected_division': division_id,
                'search_query': search_query,
            })
            
        except Exception as e:
            # Log error and return empty context
            logger.error(f"API call failed in RegistrationManagementView: {str(e)}")
            context.update({
                'registrations': [],
                'stats': {
                    'total_registrations': 0,
                    'total_free_agents': 0,
                    'divisions_count': 0,
                    'teams_count': 0,
                },
                'divisions': [],
                'leagues': League.objects.all().order_by('name'),
                'selected_league': None,
                'selected_division': None,
                'search_query': '',
            })

        return context
    template_name = 'registrations/registration_management.html'
    model = Registration
    context_object_name = 'registrations'

    def test_func(self):
        return self.request.user.is_admin()

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
        
        # Organize registrations
        organized_data = defaultdict(lambda: defaultdict(list))
        free_agents = defaultdict(list)
        
        for registration in self.get_queryset():
            if registration.player.team:
                organized_data[registration.division][registration.player.team].append(registration)
            else:
                free_agents[registration.division].append(registration)

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

@login_required
def registration_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'No session ID provided')
        return redirect('leagues:league_list')

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
            stripe_checkout_session=session_id,
            notes=player_data.get('notes', ''),
            is_late_registration=session.metadata.get('is_late_registration', 'false') == 'true',
            division_id=session.metadata['division_id']
        )

        messages.success(request, 'Registration completed successfully!')
        return redirect('leagues:league_list')
        
    except Exception as e:
        messages.error(request, f'Error processing registration: {str(e)}')
        return redirect('leagues:league_list')

@login_required
def registration_cancel(request):
    messages.error(request, 'Registration canceled')
    return redirect('leagues:league_list')
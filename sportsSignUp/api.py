from django.views.decorators.http import require_POST  # This decorator ensures the view only accepts POST requests
from django.contrib.auth.decorators import user_passes_test  # This decorator checks if user meets a condition
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import League, Player, Team


def get_teams_by_league(request, league_id):
    """API endpoint to get all teams organized by division for a league"""
    # Check if user is authenticated and is admin
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Authentication required'
        }, status=401)
    
    if not request.user.is_admin():
        return JsonResponse({
            'error': 'Admin privileges required'
        }, status=403)

    try:
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
        
    except League.DoesNotExist:
        return JsonResponse({
            'error': f'League with id {league_id} not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


def assign_team(request, player_id):
    """Handle team assignment for a player"""
    try:
        player = get_object_or_404(Player, id=player_id)
        team = get_object_or_404(Team, id=request.POST.get('team_id'))
        
        # Update the player's team
        player.team = team
        player.save()
        
        # Create a log of the division change if applicable
        old_division = None
        if hasattr(player, 'registration'):
            old_division = player.registration.division
        
        if old_division and old_division != team.division:
            messages.info(
                request, 
                f"Player moved from {old_division.name} to {team.division.name}"
            )
        
        messages.success(request, f"Successfully assigned {player.get_full_name()} to {team.name}")
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
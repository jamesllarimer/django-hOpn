from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from teams.models import Team
from players.models import Player
from leagues.models import Division
from ..serializers.serializers import TeamSerializer, PlayerSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teams_by_division(request, division_id):
    """Get all teams for a specific division"""
    division = get_object_or_404(Division, id=division_id)
    teams = Team.objects.filter(division=division)
    serializer = TeamSerializer(teams, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_player(request, team_id):
    """Assign a player to a team"""
    if not request.user.is_admin:
        return Response(
            {"error": "Only admins can assign players to teams"}, 
            status=status.HTTP_403_FORBIDDEN
        )

    team = get_object_or_404(Team, id=team_id)
    player_id = request.data.get('player_id')
    
    if not player_id:
        return Response(
            {"error": "Player ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        player = Player.objects.get(id=player_id)
        player.team = team
        player.save()
        serializer = PlayerSerializer(player)
        return Response(serializer.data)
    except Player.DoesNotExist:
        return Response(
            {"error": "Player not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_player(request, team_id, player_id):
    """Remove a player from a team"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is team captain or admin
    if not (request.user.is_admin or 
            (team.captain.user == request.user)):
        return Response(
            {"error": "Only team captains or admins can remove players"}, 
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        player = Player.objects.get(id=player_id, team=team)
        player.team = None
        player.save()
        return Response({"status": "success"})
    except Player.DoesNotExist:
        return Response(
            {"error": "Player not found in team"}, 
            status=status.HTTP_404_NOT_FOUND
        )
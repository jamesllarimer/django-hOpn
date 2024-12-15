from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from players.models import Player, FreeAgent
from teams.models import Team
from ..serializers.serializers import PlayerSerializer, FreeAgentSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_team(request, player_id):
    """Assign a player to a team"""
    if not request.user.is_admin:
        return Response(
            {"error": "Only admins can assign teams"}, 
            status=status.HTTP_403_FORBIDDEN
        )

    player = get_object_or_404(Player, id=player_id)
    team_id = request.data.get('team_id')
    
    if not team_id:
        return Response(
            {"error": "Team ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        team = Team.objects.get(id=team_id)
        player.team = team
        player.save()
        serializer = PlayerSerializer(player)
        return Response(serializer.data)
    except Team.DoesNotExist:
        return Response(
            {"error": "Team not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_free_agents(request, league_id):
    """Get all available free agents for a league"""
    free_agents = FreeAgent.objects.filter(
        league_id=league_id,
        status='AVAILABLE'
    ).order_by('-created_at')

    # Apply division filter if provided
    division_id = request.query_params.get('division')
    if division_id:
        free_agents = free_agents.filter(division_id=division_id)

    serializer = FreeAgentSerializer(free_agents, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_team_players(request, team_id):
    """Get all players for a specific team"""
    players = Player.objects.filter(team_id=team_id, is_active=True)
    serializer = PlayerSerializer(players, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_free_agent_details(request, agent_id):
    """Get detailed information about a specific free agent"""
    free_agent = get_object_or_404(FreeAgent, id=agent_id)
    serializer = FreeAgentSerializer(free_agent)
    return Response(serializer.data)
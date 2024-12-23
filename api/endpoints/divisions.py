from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from leagues.models import League, Division
from players.models import Player
from teams.models import Team
from ..serializers.serializers import DivisionSerializer, TeamSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_divisions_by_league(request, league_id):
    """Get all divisions available for a league"""
    league = get_object_or_404(League, id=league_id)
    divisions = league.available_divisions.all().order_by('name')
    serializer = DivisionSerializer(divisions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_divisions_and_teams(request, league_id):
    """Get divisions and their teams for a league"""
    league = get_object_or_404(League, id=league_id)
    divisions = league.available_divisions.all()

    data = []
    for division in divisions:
        teams = Team.objects.filter(
            league=league,
            division=division
        ).order_by('name')

        division_data = {
            'id': division.id,
            'name': division.name,
            'teams': TeamSerializer(teams, many=True).data
        }
        data.append(division_data)

    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_division_details(request, division_id):
    """Get detailed information about a specific division"""
    division = get_object_or_404(Division, id=division_id)
    data = DivisionSerializer(division).data
    
    # Add additional stats
    data['team_count'] = Team.objects.filter(division=division).count()
    data['player_count'] = Player.objects.filter(team__division=division).count()
    
    return Response(data)
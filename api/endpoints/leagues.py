from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from leagues.models import League
from ..serializers.serializers import DivisionSerializer, TeamSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_divisions_by_league(request, league_id):
    """Get all divisions for a specific league"""
    league = get_object_or_404(League, id=league_id)
    divisions = league.available_divisions.all()
    serializer = DivisionSerializer(divisions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teams_by_league(request, league_id):
    """Get all teams organized by division for a league"""
    league = get_object_or_404(League, id=league_id)
    divisions = league.available_divisions.all()
    
    data = []
    for division in divisions:
        teams = division.teams.filter(league=league)
        data.append({
            'id': division.id,
            'name': division.name,
            'teams': TeamSerializer(teams, many=True).data
        })
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_divisions_and_teams(request, league_id):
    """Get both divisions and their teams for a league"""
    league = get_object_or_404(League, id=league_id)
    divisions = league.available_divisions.prefetch_related('teams').all()
    
    data = []
    for division in divisions:
        teams = division.teams.filter(league=league)
        division_data = DivisionSerializer(division).data
        division_data['teams'] = TeamSerializer(teams, many=True).data
        data.append(division_data)
    
    return Response(data)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from registrations.models import Registration
from leagues.models import League
from ..serializers.serializers import RegistrationSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_registrations_by_league(request, league_id):
    """Get all registrations for a league with optional filters"""
    if not request.user.is_admin:
        return Response(
            {"error": "Only admins can view all registrations"}, 
            status=status.HTTP_403_FORBIDDEN
        )

    league = get_object_or_404(League, id=league_id)
    registrations = Registration.objects.filter(league=league)
    
    # Apply filters
    division_id = request.query_params.get('division')
    if division_id:
        registrations = registrations.filter(division_id=division_id)
        
    team_id = request.query_params.get('team')
    if team_id:
        registrations = registrations.filter(player__team_id=team_id)
        
    search = request.query_params.get('search', '').strip()
    if search:
        registrations = registrations.filter(
            Q(player__first_name__icontains=search) |
            Q(player__last_name__icontains=search) |
            Q(player__email__icontains=search) |
            Q(player__phone_number__icontains=search)
        )
    
    serializer = RegistrationSerializer(registrations, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_registration_stats(request, league_id):
    """Get registration statistics for a league"""
    if not request.user.is_admin:
        return Response(
            {"error": "Only admins can view registration stats"}, 
            status=status.HTTP_403_FORBIDDEN
        )

    league = get_object_or_404(League, id=league_id)
    registrations = Registration.objects.filter(league=league)
    
    stats = {
        'total_registrations': registrations.count(),
        'paid_registrations': registrations.filter(payment_status='paid').count(),
        'pending_registrations': registrations.filter(payment_status='pending').count(),
        'late_registrations': registrations.filter(is_late_registration=True).count(),
        'by_division': {}
    }
    
    # Get stats by division
    divisions = league.available_divisions.all()
    for division in divisions:
        div_regs = registrations.filter(division=division)
        stats['by_division'][division.name] = {
            'total': div_regs.count(),
            'paid': div_regs.filter(payment_status='paid').count(),
            'pending': div_regs.filter(payment_status='pending').count()
        }
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_registration_status(request, registration_id):
    """Update the payment status of a registration"""
    if not request.user.is_admin:
        return Response(
            {"error": "Only admins can update registration status"}, 
            status=status.HTTP_403_FORBIDDEN
        )

    registration = get_object_or_404(Registration, id=registration_id)
    new_status = request.data.get('status')
    
    if new_status not in ['pending', 'paid', 'cancelled', 'refunded']:
        return Response(
            {"error": "Invalid status"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    registration.payment_status = new_status
    registration.save()
    
    serializer = RegistrationSerializer(registration)
    return Response(serializer.data)
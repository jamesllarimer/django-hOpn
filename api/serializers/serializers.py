from rest_framework import serializers
from leagues.models import League, Division
from teams.models import Team
from players.models import Player, FreeAgent
from registrations.models import Registration

class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ['id', 'name', 'skill_level', 'age_group']

class TeamSerializer(serializers.ModelSerializer):
    division_name = serializers.CharField(source='division.name', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'division', 'division_name']

class PlayerSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = Player
        fields = [
            'id', 'first_name', 'last_name', 'email', 
            'phone_number', 'team', 'team_name', 'is_active'
        ]

class RegistrationSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.get_full_name', read_only=True)
    team_name = serializers.CharField(source='player.team.name', read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)

    class Meta:
        model = Registration
        fields = [
            'id', 'player_name', 'team_name', 'division_name',
            'payment_status', 'is_late_registration', 'registered_at'
        ]

class FreeAgentSerializer(serializers.ModelSerializer):
    division_name = serializers.CharField(source='division.name', read_only=True)

    class Meta:
        model = FreeAgent
        fields = [
            'id', 'first_name', 'last_name', 'email', 
            'phone_number', 'division', 'division_name', 'status'
        ]
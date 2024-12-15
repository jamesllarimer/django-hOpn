from django import forms

from players.models import Player
from .models import Team

class TeamEditForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'division', 'league']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'division': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'league': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If instance exists (editing existing team), get its current league
        if self.instance.pk:
            self.fields['division'].queryset = Division.objects.filter(
                league_sessions=self.instance.league
            )

    def clean(self):
        cleaned_data = super().clean()
        division = cleaned_data.get('division')
        league = cleaned_data.get('league')
        
        if division and league:
            # Verify division belongs to the selected league
            if league not in division.league_sessions.all():
                raise forms.ValidationError(
                    "Selected division is not available in the selected league."
                )
        return cleaned_data

class TeamSignupForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'first_name', 
            'last_name', 
            'email', 
            'phone_number',
            'parent_name',
            'date_of_birth',
            'membership_number',
            'is_member'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'parent_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded px-3 py-2'
            }),
            'membership_number': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'is_member': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields optional if needed
        self.fields['parent_name'].required = False
        self.fields['membership_number'].required = False
        self.fields['is_member'].required = False
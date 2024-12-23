from django import forms

from leagues.models import Division, League
from .models import TeamInvitation

class TeamInvitationForm(forms.ModelForm):
    class Meta:
        model = TeamInvitation
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'rows': 4,
                'placeholder': 'Add a personal message to the invitation (optional)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].required = False

class InvitationFilterForm(forms.Form):
    league = forms.ModelChoiceField(
        queryset=League.objects.all(),
        required=False,
        empty_label="All Leagues",
        widget=forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
    )
    division = forms.ModelChoiceField(
        queryset=Division.objects.none(),
        required=False,
        empty_label="All Divisions",
        widget=forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + TeamInvitation.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded px-3 py-2',
            'placeholder': 'Search by name or email...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If a league is selected, filter divisions by that league
        if 'league' in self.data:
            try:
                league_id = int(self.data.get('league'))
                self.fields['division'].queryset = Division.objects.filter(
                    league_sessions__id=league_id
                ).distinct()
            except (ValueError, TypeError):
                pass
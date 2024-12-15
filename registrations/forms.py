from django import forms
from .models import Registration

class RegistrationStatusForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['payment_status', 'notes']
        widgets = {
            'payment_status': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False

class RegistrationFilterForm(forms.Form):
    league = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
    )
    division = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded px-3 py-2',
            'placeholder': 'Search players...'
        })
    )

    def __init__(self, *args, **kwargs):
        leagues = kwargs.pop('leagues', [])
        divisions = kwargs.pop('divisions', [])
        super().__init__(*args, **kwargs)
        self.fields['league'].choices = [('', 'All Leagues')] + [
            (league.id, league.name) for league in leagues
        ]
        self.fields['division'].choices = [('', 'All Divisions')] + [
            (division.id, division.name) for division in divisions
        ]
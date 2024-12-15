
from django import forms
from .models import FreeAgent

class FreeAgentRegistrationForm(forms.ModelForm):
    class Meta:
        model = FreeAgent
        fields = [
            'first_name', 
            'last_name', 
            'email', 
            'phone_number', 
            'date_of_birth', 
            'division', 
            'membership_number', 
            'is_member', 
            'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded px-3 py-2'
            }),
            'division': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'membership_number': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'is_member': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300'}),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'rows': 4
            })
        }
        
    def __init__(self, *args, league=None, **kwargs):
        super().__init__(*args, **kwargs)
        if league:
            self.fields['division'].queryset = league.available_divisions.all()
        self.fields['notes'].required = False
        self.fields['membership_number'].required = False
from django import forms
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
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + TeamInvitation.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
    )
    date_range = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Time'),
            ('7', 'Last 7 Days'),
            ('30', 'Last 30 Days'),
            ('90', 'Last 90 Days')
        ],
        widget=forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'})
    )
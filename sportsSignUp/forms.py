from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Division, Player

class FreeAgentRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    parent_name = forms.CharField(max_length=200, required=False)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    division = forms.ModelChoiceField(queryset=Division.objects.none())
    membership_number = forms.CharField(max_length=50, required=True)
    is_member = forms.BooleanField(required=False, initial=False)
    notes = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text="Any additional information you'd like us to know"
    )

    def __init__(self, *args, **kwargs):
        league = kwargs.pop('league', None)
        super().__init__(*args, **kwargs)
        if league:
            self.fields['division'].queryset = league.available_divisions.all()

class TeamSignupForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'first_name', 
            'last_name', 
            'email', 
            'phone_number',
            'parent_name',  # if this is optional
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
        
                    
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=True, max_length=20)
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'date_of_birth', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.date_of_birth = self.cleaned_data['date_of_birth']
        if commit:
            user.save()
        return user
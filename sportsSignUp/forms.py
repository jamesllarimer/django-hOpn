from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Division, FreeAgent, Player, Team

class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'division']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'placeholder': 'Enter team name'
            }),
            'division': forms.Select(attrs={
                'class': 'w-full border rounded px-3 py-2'
            })
        }

    def __init__(self, *args, league=None, **kwargs):
        super().__init__(*args, **kwargs)
        if league:
            # Only show divisions available for this league
            self.fields['division'].queryset = league.available_divisions.all()
            self.instance.league = league  # Set the league for the team

    def clean_name(self):
        name = self.cleaned_data.get('name')
        league = self.instance.league
        
        # Check if a team with this name already exists in the league
        if Team.objects.filter(name=name, league=league).exists():
            raise forms.ValidationError("A team with this name already exists in this league.")
        
        return name
    
class FreeAgentRegistrationForm(forms.ModelForm):
    class Meta:
        model = FreeAgent
        fields = ['first_name', 'last_name', 'email', 'phone_number', 
                 'date_of_birth', 'division', 'membership_number', 
                 'is_member', 'notes']
        
    def __init__(self, *args, league=None, **kwargs):
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
    

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_of_birth']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded px-3 py-2'
            }),
        }
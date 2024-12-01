from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Division

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
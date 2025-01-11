from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Division, FreeAgent, Player, Team, DynamicForm, FormField, FormResponse, League
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.forms import modelformset_factory
import json

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

class DynamicFormManagementView(UserPassesTestMixin, ListView):
    model = DynamicForm
    template_name = 'forms/form_management.html'
    context_object_name = 'forms'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['leagues_without_forms'] = League.objects.exclude(
            id__in=DynamicForm.objects.values_list('league_id', flat=True)
        )
        return context

class FormFieldForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = ['label', 'field_type', 'required', 'placeholder', 
                 'help_text', 'options', 'validation_rules', 'order']
        widgets = {
            'options': forms.Textarea(attrs={'rows': 3, 
                'placeholder': '["Option 1", "Option 2", "Option 3"]'}),
            'validation_rules': forms.Textarea(attrs={'rows': 3, 
                'placeholder': '{"min_length": 5, "max_length": 50}'}),
        }

    def clean_options(self):
        options = self.cleaned_data.get('options')
        if options:
            try:
                return json.loads(options)
            except json.JSONDecodeError:
                raise forms.ValidationError('Invalid JSON format')
        return options

    def clean_validation_rules(self):
        rules = self.cleaned_data.get('validation_rules')
        if rules:
            try:
                return json.loads(rules)
            except json.JSONDecodeError:
                raise forms.ValidationError('Invalid JSON format')
        return rules

class DynamicFormCreateView(UserPassesTestMixin, CreateView):
    model = DynamicForm
    template_name = 'forms/form_create.html'
    fields = ['title', 'description']
    
    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        league_id = self.kwargs.get('league_id')
        form.instance.league = get_object_or_404(League, id=league_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('form_edit', kwargs={'pk': self.object.pk})

class DynamicFormEditView(UserPassesTestMixin, UpdateView):
    model = DynamicForm
    template_name = 'forms/form_edit.html'
    fields = ['title', 'description', 'is_active']

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        FormFieldFormSet = modelformset_factory(
            FormField, 
            form=FormFieldForm,
            extra=1,
            can_delete=True
        )
        
        if self.request.POST:
            context['formfield_formset'] = FormFieldFormSet(
                self.request.POST,
                queryset=FormField.objects.filter(form=self.object)
            )
        else:
            context['formfield_formset'] = FormFieldFormSet(
                queryset=FormField.objects.filter(form=self.object)
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formfield_formset = context['formfield_formset']
        
        if formfield_formset.is_valid():
            self.object = form.save()
            formfield_formset.instance = self.object
            formfield_formset.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

class RegistrationFormView(CreateView):
    model = FormResponse
    template_name = 'forms/registration_form.html'
    
    def get_form_class(self):
        # Dynamically create form class based on form fields
        dynamic_form = get_object_or_404(
            DynamicForm, 
            league_id=self.kwargs['league_id'],
            is_active=True
        )
        
        class DynamicRegistrationForm(forms.Form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for field in dynamic_form.fields.all():
                    field_kwargs = {
                        'label': field.label,
                        'required': field.required,
                        'help_text': field.help_text,
                    }
                    
                    if field.placeholder:
                        field_kwargs['widget'] = forms.TextInput(
                            attrs={'placeholder': field.placeholder}
                        )
                    
                    if field.field_type == 'text':
                        self.fields[f'field_{field.id}'] = forms.CharField(**field_kwargs)
                    elif field.field_type == 'textarea':
                        self.fields[f'field_{field.id}'] = forms.CharField(
                            widget=forms.Textarea,
                            **field_kwargs
                        )
                    elif field.field_type == 'number':
                        self.fields[f'field_{field.id}'] = forms.IntegerField(**field_kwargs)
                    elif field.field_type == 'email':
                        self.fields[f'field_{field.id}'] = forms.EmailField(**field_kwargs)
                    elif field.field_type == 'date':
                        self.fields[f'field_{field.id}'] = forms.DateField(
                            widget=forms.DateInput(attrs={'type': 'date'}),
                            **field_kwargs
                        )
                    elif field.field_type == 'checkbox':
                        self.fields[f'field_{field.id}'] = forms.BooleanField(**field_kwargs)
                    elif field.field_type in ['select', 'radio']:
                        choices = [(opt, opt) for opt in field.options]
                        if field.field_type == 'select':
                            self.fields[f'field_{field.id}'] = forms.ChoiceField(
                                choices=choices,
                                **field_kwargs
                            )
                        else:
                            self.fields[f'field_{field.id}'] = forms.ChoiceField(
                                widget=forms.RadioSelect,
                                choices=choices,
                                **field_kwargs
                            )
                    elif field.field_type == 'file':
                        self.fields[f'field_{field.id}'] = forms.FileField(**field_kwargs)

        return DynamicRegistrationForm

    def form_valid(self, form):
        dynamic_form = get_object_or_404(
            DynamicForm, 
            league_id=self.kwargs['league_id'],
            is_active=True
        )
        
        # Create response object
        response = FormResponse.objects.create(
            form=dynamic_form,
            user=self.request.user,
            responses=form.cleaned_data
        )
        
        # Continue with registration process
        return redirect('registration_payment', league_id=self.kwargs['league_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league'] = get_object_or_404(League, id=self.kwargs['league_id'])
        return context
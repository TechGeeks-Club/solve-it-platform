from django import forms
from .models import Team
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms.widgets import Input


from django.contrib.auth.forms import AuthenticationForm

class TeamCreationForm(forms.ModelForm):

    class Meta:
        model = Team
        fields = ['name','password']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter team name',
            }),
            'password': forms.PasswordInput(attrs={
                'type':"password",
                'class': 'form-input',
                'placeholder': 'Enter password',
            }),
        }

# ? i create it becouse i couldn't use the first one in the participant form
class TeamForm(forms.Form):
    teamName = forms.CharField(max_length=70, required=True, label= 'Team Name')
    teamPassword = forms.CharField(max_length=128, required=True, label='Team Password', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['teamName'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter team name',
        })
        self.fields['teamPassword'].widget.attrs.update({
            'type' : 'password',
            'class': 'form-input',
            'placeholder': 'Enter team password',
        })


class CreateUserForm(UserCreationForm):    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter username',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter first name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter last name',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm password',
        })
        self.fields['password1'].widget.attrs.pop('autocomplete', None)
        self.fields['password2'].widget.attrs.pop('autocomplete', None)


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add or override classes for the username field
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter your username',
        })
        # Add or override classes for the password field
        self.fields['password'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter your password',
        })
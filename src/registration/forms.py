from django import forms
from .models import Team
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class TeamCreationForm(forms.ModelForm):

    class Meta:
        model = Team
        fields = ['name','password']

# ? i create it becouse i couldn't use the first one in the participant form
class TeamForm(forms.Form):
    teamName = forms.CharField(max_length=70, required=True, label= 'Team Name')
    teamPassword = forms.CharField(max_length=128, required=True, label='Team Password')

class CreateUserForm(UserCreationForm):    
    class Meta:
        model = User
        fields = ['username','first_name','last_name','password1', 'password2']
    #? It's by default not superuser   
from django.http import HttpRequest
from django.shortcuts import render
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import login,logout,authenticate
from django.shortcuts import redirect
from django.contrib import messages

from django.contrib.auth.decorators import login_required



from .forms import CustomAuthenticationForm, TeamCreationForm,TeamForm,CreateUserForm

from .models import Team,Participant




def createTeamView(request:HttpRequest):
    form = TeamCreationForm(request.POST or None)
    if request.method == "POST" :
        try :
            with transaction.atomic():
                if( form.is_valid() ):
                    form.save()
                    return redirect("home")
                else :
                    messages.error(request, "Form validation failed. Please verify your inputs.")

        except Exception as exp:
            messages.error(request, f"{exp}")

    context = {
        "form" : form,        
    }

    return render(request,"registration/createTeam.html",context)



def getTeam(teamForm:TeamForm):
    try:
        dbTeam = Team.objects.get(name=teamForm.data["teamName"])
    except :    
        raise ValidationError("Team didn't exist, check the team name please")
    if not check_password(teamForm.data["teamPassword"], dbTeam.password):
        raise ValidationError("Team password is wrong")
    return dbTeam

def createParticipantView(request:HttpRequest):
    userForm = CreateUserForm(request.POST or None)
    teamForm = TeamForm(request.POST or None)

    if request.method == "POST" :
        try :
            with transaction.atomic():
                teamObj = getTeam(teamForm)
                if( userForm.is_valid() ):
                    userObj = userForm.save()
                    Participant(user=userObj, team=teamObj).save()
                    return redirect("home")
                else :
                    messages.error(request, "Form validation failed. Please verify your inputs.")
        except Exception as exp:
            msg = exp.__str__()[2:-2]
            messages.error(request, msg)
    
    context = {
        "teamForm" : teamForm,        
        "userForm" : userForm,        
    }

    return render(request,"registration/signup.html",context)


def participantLoginView(request : HttpRequest):
    form = CustomAuthenticationForm(request,request.POST or None)

    context = {
        "form" : form,
    }

    if request.method == "POST" :
        if( form.is_valid() ):
            try :
                login(request, form.get_user())
                context = {
                    "form" : form,
                }
                return redirect("tasksDisplay")
            except Exception as e :
                messages.error(request, f"An error occurred: {e}")
        else :
            messages.error(request, "Form validation failed. Please verify your inputs.")
    return render(request,"registration/login.html",context)


# def participantLoginView(request: HttpRequest):
#     if request.method == "POST":
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         print(username, password)
        
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect('home')
#         else:
#             context = {
#                 "status": "Invalid credentials",
#             }
#             return render(request, "registration/login.html", context)
#     return render(request, "registration/login.html")



@login_required
def logoutview(request: HttpRequest):
    logout(request)
    return redirect('home')

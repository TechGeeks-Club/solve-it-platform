from django.http import HttpRequest
from django.shortcuts import render
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import login,logout,authenticate
from django.shortcuts import redirect
from django.contrib import messages

<<<<<<< HEAD

from .forms import TeamCreationForm,TeamForm,CreateUserForm, CustomAuthenticationForm
=======
from django.contrib.auth.decorators import login_required



from .forms import TeamCreationForm,TeamForm,CreateUserForm
>>>>>>> 3150fb55588b3e716615345b2aeebd76fab3fd46

from .models import Team,Participant




def createTeamView(request:HttpRequest):
    form = TeamCreationForm(request.POST or None)
    err = None
    if request.method == "POST" :
        try :
            with transaction.atomic():
                if( form.is_valid() ):
                    form.save()
                    return redirect("home")
        except Exception as exp:
            err = exp.__str__()
    
    context = {
        "form" : form,        
        "err" : err
    }

    return render(request,"registration/createTeam.html",context)



def getTeam(teamForm:TeamForm):
    try:
        dbTeam = Team.objects.get(name=teamForm.data["teamName"])
    except :    
        raise ValidationError("Team didn't exist, maybe the team name is wrong")
    if not check_password(teamForm.data["teamPassword"], dbTeam.password):
        raise ValidationError("Team password is wrong")
    return dbTeam

def createParticipantView(request:HttpRequest):

    userForm = CreateUserForm(request.POST or None)
    teamForm = TeamForm(request.POST or None)
    err = None

    if request.method == "POST" :
        try :
            with transaction.atomic():
                if( userForm.is_valid() ):
                    teamObj = getTeam(teamForm)
                    userObj = userForm.save()
                    Participant(user=userObj, team=teamObj).save()
                    return redirect("home")
        except Exception as exp:
            err = exp.__str__()[2:-2]
    
    context = {
        "teamForm" : teamForm,        
        "userForm" : userForm,        
        "err" : err
    }

<<<<<<< HEAD
    return render(request,"registration/createParticipant.html",context)


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
                return render(request,"registration/participantLogin.html",context)
        else :
            messages.error(request, "Form validation failed. Please verify your inputs.")
    return render(request,"registration/participantLogin.html",context)
=======
    return render(request,"registration/signup.html",context)


# def participantLoginView(request : HttpRequest):
#     form = AuthenticationForm(request,request.POST or None)

#     if request.method == "POST" :
#         if( form.is_valid() ):
#             login(request, form.get_user())
#             context = {
#                 "form" : form,
#                 "status" : "Succed",
#             }
#             return render(request,"registration/login.html",context)
#     context = {
#         "form" : form,
#         "status" : "loading",
#     }
#     return render(request,"registration/login.html",context)

# from django.contrib.auth import authenticate, login
# from django.http import HttpRequest, HttpResponse
# from django.shortcuts import render, redirect

def participantLoginView(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username, password)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            context = {
                "status": "Invalid credentials",
            }
            return render(request, "registration/login.html", context)
    return render(request, "registration/login.html")



@login_required
def logoutview(request: HttpRequest):
    logout(request)
    return redirect('home')
>>>>>>> 3150fb55588b3e716615345b2aeebd76fab3fd46

from django.http import HttpRequest
from django.shortcuts import render
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import login,logout,authenticate
from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required

from django.contrib import messages



from .forms import TeamCreationForm,TeamForm,CreateUserForm

from .models import Team,Participant




def createTeamView(request:HttpRequest):
    if not request.user.is_authenticated:

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

    return redirect('tasksDisplay')
    




def getTeam(teamForm:TeamForm):
    try:
        dbTeam = Team.objects.get(name=teamForm.data["teamName"])
    except :    
        raise ValidationError("Team didn't exist, maybe the team name is wrong")
    if not check_password(teamForm.data["teamPassword"], dbTeam.password):
        raise ValidationError("Team password is wrong")
    return dbTeam

def createParticipantView(request:HttpRequest):
    if not request.user.is_authenticated:

        userForm = CreateUserForm(request.POST or None)
        teamForm = TeamForm(request.POST or None)
        err = None

        if request.method == "POST" :
            try :
                with transaction.atomic():
                    teamObj = getTeam(teamForm)

                    if( userForm.is_valid() ):
                        userObj = userForm.save()
                        Participant(user=userObj, team=teamObj).save()
                        login(request, userObj)
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
    
    return redirect('tasksDisplay')


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
    if not request.user.is_authenticated:
        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')
            print(username, password)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                
                messages.error(request, "Form validation failed. Please verify your inputs.")
                return render(request, "registration/login.html")
        return render(request, "registration/login.html")
    return redirect('home')


@login_required
def logoutview(request: HttpRequest):
    logout(request)
    return redirect('home')
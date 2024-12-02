import os
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpRequest, Http404, HttpResponse,FileResponse
from django.db import transaction
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.conf import settings


from .models import Phase,Task,TaskSolution,TaskTest,ThirdPhaseCode
from registration.models import Participant


@login_required
def tasksDisplayView(request:HttpRequest):
    phases = Phase.objects.prefetch_related("phase_tasks","phase_tasks__category","phase_tasks__task_solutions")
    context = {
        "phases" : phases
    }
    return render(request,"tasks/allChallengesDisplay.html",context)

# ? Check if team already participate in task
def checkParticipationExistance(task:Task, participant:Participant):
    try :
        solutionObj = TaskSolution.objects.get(task=task, participant__team=participant.team)
        return solutionObj
    except :
        return None

@login_required
def taskView(request:HttpRequest, task_id:int):
    print(f" [[ For Debug :  CALLED ]] ")
    task_tests_query = TaskTest.objects.filter(display=True)
    taskObj = Task.objects.prefetch_related(Prefetch('task_tests', queryset=task_tests_query)).get(id=task_id)

    participantObj = Participant.objects.get(user = request.user)
    solutionObj = checkParticipationExistance(taskObj,participantObj)

    context = {
        "task" : taskObj,
        "solution" : solutionObj,
    }
    if request.method == "POST" :
        print(f" [[ For Debug : {request.FILES} ]] ")

    return render(request,"tasks/challenge-detailes.html",context)

    # ! This work is not ready yet
    # if request.method == "POST" :
#         try :
#             with transaction.atomic():
                    #? it means they never paticipate in this task

#                 if solutionObj is not None :
#                     if solutionObj.tries < 3 :
#                         solutionObj.code = # ! HERE CODE PART 
#                         solutionObj.tries = solutionObj.tries + 1
#                         solutionObj.save()
#                     else :
#                         err = "You already use all your chances"
#                 else :
#                     TaskSolution(
#                         task= taskObj,
#                         participant=participantObj,
#                         team=participantObj.team,
#                         code= #! HERE CODE PART
#                     ).save(
#         except Exception as exp :
#             err = exp.__str__()

@login_required
def thirdPhaseView(request:HttpRequest ):
    
    # ? get the phase and see if it's locked
    try :
        # ! I CAN'T USE THE ID TO GET PHASE 3, SO IF THEY CHANGE THE NAME YOU SHOULD CHANGE IT HERE ALSO 
        phaseObj = Phase.objects.get(name = "phase 3") 
        if phaseObj.is_locked :
            return redirect("tasksDisplay")
    except Exception as exp :
        return redirect("tasksDisplay")

    
    if request.method == "POST" :
        inputCode = request.POST.get('code')
        try :
            
            codeObj = ThirdPhaseCode.objects.get(id=inputCode)
            participantObj = Participant.objects.get(user = request.user)

            if checkParticipationExistance(codeObj.task,participantObj) :
                if codeObj.result.lower() == "win" :
                    TaskSolution(
                        task = codeObj.task,
                        participant = participantObj,
                        team = participantObj.team,
                        is_corrected = True,
                        score = 100 - (codeObj.hints_value*100)/codeObj.task.points
                    ).save()
                else :
                    # ? If he lose he i'll get mines
                    TaskSolution(
                        task = codeObj.task,
                        participant = participantObj,
                        team = participantObj.team,
                        is_corrected = True,
                        score = -1 * (codeObj.hints_value*100)/codeObj.task.points
                    ).save()
            
            else :
                messages.error(request, "You already sent the code of this task")
            
            # ? Here i return the next task infrmations anyway becouse they may forget it and they use the old code only to get it
            context = {
                "nextTask" : codeObj.task.nextTask
            }
            return render(request,"tasks/thiredPhase.html",context)
        except Exception as exp :
            messages.error(request, "Code didn't exist")

    return render(request,"tasks/thiredPhase.html")

@login_required
def tasksFileDownload(request:HttpRequest):
    file_path = os.path.join(settings.MEDIA_ROOT, "tasks.c")
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    raise Http404
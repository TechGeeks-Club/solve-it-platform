from django.contrib import messages
from django.shortcuts import render
from django.http import HttpRequest
from django.db import transaction
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect




from .models import Phase,Task,TaskSolution,TaskTest,ThirdPhaseCode
from registration.models import Participant


@login_required
def tasksDisplayView(request:HttpRequest):
    phases = Phase.objects.prefetch_related("phase_tasks","phase_tasks__category")
    context = {
        "phases" : phases
    }
    return render(request,"tasks/challenges-page.html",context)

def checkParticipationExistance(task:Task, participant:Participant):
    try :
        solutionObj = TaskSolution.objects.get(task=task, participant__team=participant.team)

        return solutionObj
    except :
        return None

@login_required
def taskView(request:HttpRequest, task_id:int):
    
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
def thirdPhaseView(request:HttpRequest, ):
    if Phase.objects.get(name = "phase3").is_locked :
        return redirect("tasksDisplay")
    
    if request.method == "POST" :
        inputCode = request.POST.get('code')
        try :
            codeObj = ThirdPhaseCode.objects.get(id=inputCode)
            participantObj = Participant.objects.get(user = request.user)
            if codeObj.result.lower() == "win" :
                TaskSolution(
                    task = codeObj.task,
                    participant = participantObj,
                    team = participantObj.team,
                    is_corrected = True,
                    score = codeObj.task.points - codeObj.hints_value
                )
            else :
                TaskSolution(
                    task = codeObj.task,
                    participant = participantObj,
                    team = participantObj.team,
                    is_corrected = True,
                    score = -1 * codeObj.hints_value
                )
            
            nextTask = codeObj.task.nextTask
            context = {
                "nextTask" : nextTask
            }
            return render(request,"tasks/thiredPhase.html",context)
        
        except Exception as exp :
            messages.error(request, "Code didn't exist")
            return render(request,"tasks/thiredPhase.html")


    return render(request,"tasks/thiredPhase.html")

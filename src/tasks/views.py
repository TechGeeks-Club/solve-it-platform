from django.shortcuts import render
from django.http import HttpRequest
from django.db import transaction
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required


from .models import Phase,Task,TaskSolution,TaskTest

from registration.models import Participant,Team


@login_required
def tasksDisplayView(request:HttpRequest):
    phases = Phase.objects.prefetch_related("phase_tasks","phase_tasks__category")
    context = {
        "phases" : phases
    }
    return render(request,"tasks/challenges-page.html",context)


# def checkParticipationExistance(task:Task, participant:Participant):
#     try :
#         solutionObj = TaskSolution.objects.get(task=task, participant__team=participant.team)
#         return solutionObj
#     except :
#         return None


@login_required
def taskView(request:HttpRequest, task_id:int):
    
    # task_tests_query = TaskTest.objects.filter(display=True)
    # taskObj = Task.objects.prefetch_related(Prefetch('task_tests', queryset=task_tests_query)).get(id=task_id)

    
    
    # solutionObj = checkParticipationExistance(taskObj,participantObj)
    task = Task.objects.get(id=task_id)
    participant = Participant.objects.get(user = request.user)
    tasksolution = TaskSolution.objects.filter(task=task,team=participant.team)


    context = {"task" : task,}
    context["tasksolution"] = True if tasksolution else False
    
    
    if request.method == "POST" :
                
        if not tasksolution:
        
            if "uploadedFile" in request.FILES :
                file = request.FILES['uploadedFile']
                try :
                    with transaction.atomic():
                        TaskSolution(
                            task= task,
                            participant=participant,
                            team=participant.team,
                            code= file
                        ).save()  
                        context["tasksolution"] = True 

                except Exception as exp :
                    err = exp.__str__()

                return render(request,"tasks/challenge-detailes.html",context)

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


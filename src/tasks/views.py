from django.shortcuts import render
from django.http import HttpRequest
from django.db import transaction

from .models import Phase,Task,TaskSolution
from registration.models import Participant



def tasksDisplayView(request:HttpRequest):
    phases = Phase.objects.prefetch_related("phase_tasks","phase_tasks__category")
    context = {
        "phases" : phases
    }
    return render(request,"tasks/displayTasks.html",context)


def checkParticipationExistance(task:Task, participant:Participant):
    try :
        solutionObj = TaskSolution.objects.get(task=task, participant__team=participant.team)
        return solutionObj
    except :
        return None
        

def taskView(request:HttpRequest, task_id:int):
    pass

    # ! This work is not ready yet
    # taskObj = Task.objects.get(id=task_id)
    # err = None

    # if request.method == "POST" :
    #     # ? i don't want the access to this page to require authentication, just the code submition
    #     if request.user.is_authenticated :
    #         try :
    #             with transaction.atomic():
                    
    #                 participantObj = Participant.objects.get(user = request.user)
    #                 # ? to see if it participate before in that task 
    #                 solutionObj = checkParticipationExistance(taskObj,participantObj)
                    
    #                 if solutionObj is not None :
    #                     if solutionObj.tries < 3 :
                            
    #                         # ! HERE CODE PART
    #                         solutionObj.code = 
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
    #                     ).save()

    #                     # TaskSolutionForm.save(task=taskObj ,participant=participantObj)
            
    #         except Exception as exp :
    #             err = exp.__str__()
    #     else :
    #         err = "User is not authenticated"

    # context = {
    #     "taskObj" : taskObj,
    #     "err" : err
    # }
    # # return render(request,"tasks/task.html",context) #! ma dirch el errors hak , dir bel function hadi ==> messages.error(request, err)

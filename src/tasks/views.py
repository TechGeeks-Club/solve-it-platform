from django.shortcuts import render
from django.http import HttpRequest
from django.db import transaction
from django.db.models import Prefetch

from .models import Phase,Task,TaskSolution,TaskTest
from registration.models import Participant



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
        

def taskView(request:HttpRequest, task_id:int):
    task_tests_query = TaskTest.objects.filter(display=True)
    taskObj = Task.objects.prefetch_related(Prefetch('task_tests', queryset=task_tests_query)).get(id=task_id)
    solutionObj = None
    try:
        solutionObj = TaskSolution.objects.get(task=taskObj)
    except :
        pass

    err = None

    context = {
        "task" : taskObj,
        "solution" : solutionObj,
        "err" : err
    }

    return render(request,"tasks/task.html",context)
    # ! This work is not ready yet

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


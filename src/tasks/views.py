from django.shortcuts import render,redirect
from django.http import HttpRequest
from django.db import transaction
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required


from .models import Phase,Task,TaskSolution,TaskTest,ThirdPhaseCode

from registration.models import Participant,Team

import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.contrib import messages



@login_required
def tasksDisplayView(request:HttpRequest):
    phases = Phase.objects.prefetch_related("phase_tasks","phase_tasks__category","phase_tasks__task_solutions")
    context = {
        "phases" : phases
    }
    return render(request,"tasks/challenges-page.html",context)


def checkParticipationExistance(task:Task, participant:Participant):
    try :
        solutionObj = TaskSolution.objects.get(task=task, participant__team=participant.team)
        print(solutionObj)
        return solutionObj
    except :
        return None


@login_required
def taskView(request:HttpRequest, task_id:int):
    
    # task_tests_query = TaskTest.objects.filter(display=True)
    # taskObj = Task.objects.prefetch_related(Prefetch('task_tests', queryset=task_tests_query)).get(id=task_id)

    
    
    # solutionObj = checkParticipationExistance(taskObj,participantObj)
    
    task = Task.objects.get(id=task_id)
    
    # ? get the phase and see if it's locked
    try :
        # ! I CAN'T USE THE ID TO GET PHASE 3, SO IF THEY CHANGE THE NAME YOU SHOULD CHANGE IT HERE ALSO 
        phaseObj = Phase.objects.get(name = task.phase.name) 
        if phaseObj.is_locked :
            return redirect("tasksDisplay")
    except Exception as exp :
        return redirect("tasksDisplay")
    
    
    participant = Participant.objects.get(user = request.user)
    tasksolution = TaskSolution.objects.filter(task=task,team=participant.team)


    context = {"task" : task,}
    context["tasksolution"] = True if tasksolution else False
    
    if not checkParticipationExistance(task,participant) :
        if request.method == "POST" :
                

        
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
        else : #! GET
            return render(request,"tasks/challenge-detailes.html",context)
     
    else:
        return redirect("tasksDisplay")


    
    



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

            if not checkParticipationExistance(codeObj.task,participantObj) :
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
    file_path = os.path.join(settings.MEDIA_ROOT, "tasks.rar")
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    raise Http404
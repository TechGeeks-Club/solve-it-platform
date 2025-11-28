from django.shortcuts import render,redirect
from django.http import HttpRequest
from django.db import transaction
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.utils import timezone


from .models import Phase,Task,TaskSolution,TaskTest,ThirdPhaseCode
from .kafka_producer import send_submission_sync

from registration.models import Participant,Team

import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.contrib import messages



@login_required
def tasksDisplayView(request:HttpRequest):
    try:
        phase = Phase.objects.get(is_locked=False)
        print("donn")
    except:
        messages.error(request, "wait please")
        return redirect("home")
    if phase.name == "phase 3" :
        return redirect("thirdPhase")
    
    
    tasks = Task.objects.filter(phase=phase).prefetch_related('task_solutions')
    # print(tasks.all()[3].task_solutions)
    
    
    # tasks = phase.prefetch_related("phase_tasks","phase_tasks__category","phase_tasks__task_solutions")
    # task = Task.objects.filter(phase=phase)
    
    # phases = Phase.objects.prefetch_related("phase_tasks","phase_tasks__category","phase_tasks__task_solutions")
    context = {
        "tasks" : tasks,
        "phase" : phase
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
            # Handle both file upload and direct code submission
            code_content = None
            language_id = int(request.POST.get('language_id', 50))  # Default to C
            
            if "uploadedFile" in request.FILES :
                file = request.FILES['uploadedFile']
                try:
                    code_content = file.read().decode('utf-8')
                except Exception as e:
                    messages.error(request, f"Error reading file: {str(e)}")
                    return render(request,"tasks/challenge-detailes.html",context)
            elif "code" in request.POST:
                code_content = request.POST.get('code')
            
            if code_content:
                try :
                    with transaction.atomic():
                        # Create submission record
                        submission = TaskSolution(
                            task=task,
                            participant=participant,
                            team=participant.team,
                            code=code_content,
                            language_id=language_id,
                            status='pending',
                            kafka_sent_at=timezone.now()
                        )
                        submission.save()
                        
                        # Send to Kafka for async processing
                        kafka_sent = send_submission_sync(
                            submission_id=submission.id,
                            task_id=task.id,
                            user_id=participant.user.id,
                            team_id=participant.team.id,
                            code=code_content,
                            language_id=language_id
                        )
                        
                        if kafka_sent:
                            submission.status = 'processing'
                            submission.save()
                            messages.success(
                                request,
                                "Submission received! Your code is being evaluated..."
                            )
                        else:
                            messages.warning(
                                request,
                                "Submission saved but evaluation service is unavailable. "
                                "It will be processed when the service is back online."
                            )
                        
                        context["tasksolution"] = True 

                except Exception as exp :
                    messages.error(request, f"Error submitting code: {str(exp)}")

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
                    
                    
                    loseScore = (((55*codeObj.task.points)/100 + codeObj.hints_value) *100)/codeObj.task.points
                    
                    
                    TaskSolution(
                        task = codeObj.task,
                        participant = participantObj,
                        team = participantObj.team,
                        is_corrected = True,
                        score = -1 * loseScore
                    ).save()              
                    
                    # TaskSolution(
                    #     task = codeObj.task,
                    #     participant = participantObj,
                    #     team = participantObj.team,
                    #     is_corrected = True,
                    #     score = -1 * (codeObj.hints_value*100)/codeObj.task.points
                    # ).save()
            
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
from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import logging
from django.conf import settings

from .models import Phase, Task, TaskSolution, Settings
from .kafka_producer import send_submission_sync

from registration.models import Participant, Team

import os
from django.conf import settings

logger = logging.getLogger(__name__)
from django.http import FileResponse, Http404
from django.contrib import messages


@login_required
def tasksDisplayView(request: HttpRequest):
    from django.core.cache import cache
    # Cache only the list of unlocked phase IDs
    unlocked_phase_ids = cache.get(settings.CACHE_UNLOCKED_PHASE_IDS_KEY)
    if unlocked_phase_ids is None:
        unlocked_phase_ids = list(Phase.objects.filter(is_locked=False).values_list('id', flat=True))
        cache.set(settings.CACHE_UNLOCKED_PHASE_IDS_KEY, unlocked_phase_ids)
    phases = Phase.objects.filter(id__in=unlocked_phase_ids)

    # Get current user's team
    try:
        participant = Participant.objects.get(user=request.user)
        user_team = participant.team
    except:
        messages.error(request, "You must be part of a team to view challenges")
        return redirect("home")

    # Get tasks with solutions for the user's team, only for unlocked phases
    tasks = Task.objects.filter(phase__in=phases).prefetch_related("task_solutions")

    # Get settings for pass/fail logic
    settings_obj = Settings.get_settings()

    # Add solution info for each task
    tasks_with_status = []
    for task in tasks:
        task_solution = task.task_solutions.filter(team=user_team).first()

        # Determine status based on database status field and threshold
        status_text = None
        status_class = None
        status_val = "unsolved"
        if task_solution:
            if task_solution.status == "completed":
                status_text = "Success"
                status_class = "success"
                status_val = "solved completed"
            elif task_solution.status == "failed":
                status_text = "Failed"
                status_class = "failed"
                status_val = "unsolved failed"
            elif task_solution.status == "processing":
                status_text = "In Progress"
                status_class = "in-progress"
                status_val = "unsolved"
            elif not task_solution.is_corrected:
                status_text = "In Progress"
                status_class = "in-progress"
                status_val = "unsolved"
        else:
            status_val = "unsolved"

        tasks_with_status.append(
            {
                "task": task,
                "solution": task_solution,
                "attempts": task_solution.attempts if task_solution else 0,
                "max_attempts": settings_obj.max_attempts,
                "can_access": task_solution is None
                or task_solution.attempts < settings_obj.max_attempts,
                "status_text": status_text,
                "status_class": status_class,
                "score": task_solution.score if task_solution else 0,
                "is_corrected": task_solution.is_corrected if task_solution else False,
                "status_val": status_val,
            }
        )

    context = {
        "tasks_with_status": tasks_with_status,
        "phases": phases,
        "max_attempts": settings_obj.max_attempts,
        "pass_threshold": settings_obj.pass_threshold,
    }

    return render(request, "tasks/challenges-page.html", context)


def checkParticipationExistance(task: Task, participant: Participant):
    try:
        solutionObj = TaskSolution.objects.get(
            task=task, participant__team=participant.team
        )
        print(solutionObj)
        return solutionObj
    except:
        return None


@login_required
def taskView(request: HttpRequest, task_id: int):
    # task_tests_query = TaskTest.objects.filter(display=True)
    # taskObj = Task.objects.prefetch_related(Prefetch('task_tests', queryset=task_tests_query)).get(id=task_id)

    # solutionObj = checkParticipationExistance(taskObj,participantObj)

    task = Task.objects.get(id=task_id)

    # ? get the phase and see if it's locked
    try:
        # ! I CAN'T USE THE ID TO GET PHASE 3, SO IF THEY CHANGE THE NAME YOU SHOULD CHANGE IT HERE ALSO
        phaseObj = Phase.objects.get(name=task.phase.name)
        if phaseObj.is_locked:
            return redirect("tasksDisplay")
    except Exception:
        return redirect("tasksDisplay")

    participant = Participant.objects.get(user=request.user)

    # Get or create TaskSolution for this team/task (only one per team/task)
    tasksolution = TaskSolution.objects.filter(task=task, team=participant.team).first()

    # Get platform settings for max attempts
    settings_obj = Settings.get_settings()
    max_attempts = settings_obj.max_attempts

    # Calculate remaining attempts
    current_attempts = tasksolution.attempts if tasksolution else 0
    remaining_attempts = max_attempts - current_attempts

    # Check if submission is still processing
    is_processing = tasksolution and tasksolution.status == "processing"

    # Check if team has Time Machine power and can use it
    from .power_handlers import get_power_handler

    has_time_machine = False
    time_machine_used = False

    if tasksolution and remaining_attempts <= 0:
        TimeMachine = get_power_handler("time_machine")
        if TimeMachine:
            can_use, reason = TimeMachine.can_use(
                team=participant.team, task=task, tasksolution=tasksolution
            )
            has_time_machine = can_use
            time_machine_used = "already used" in reason.lower()

    context = {
        "task": task,
        "tasksolution": tasksolution,
        "current_attempts": current_attempts,
        "max_attempts": max_attempts,
        "remaining_attempts": remaining_attempts,
        "can_submit": remaining_attempts > 0 and not is_processing,
        "has_time_machine": has_time_machine,
        "time_machine_used": time_machine_used,
    }

    if request.method == "POST":
        # Check if submission is still processing
        if is_processing:
            messages.warning(
                request,
                "Your previous submission is still being evaluated. Please wait.",
            )
            return render(request, "tasks/challenge-detailes.html", context)

        # Check if attempts limit reached
        if tasksolution and tasksolution.attempts >= max_attempts:
            messages.error(
                request,
                f"Maximum submission attempts ({max_attempts}) reached for this task.",
            )
            return render(request, "tasks/challenge-detailes.html", context)

        # Handle both file upload and direct code submission
        code_content = None

        if "uploadedFile" in request.FILES:
            file = request.FILES["uploadedFile"]
            try:
                code_content = file.read().decode("utf-8")
            except Exception as e:
                messages.error(request, f"Error reading file: {str(e)}")
                return render(request, "tasks/challenge-detailes.html", context)
        elif "code" in request.POST:
            code_content = request.POST.get("code")

        if code_content:
            try:
                logger.info(
                    f"Received code submission for task {task.id} from user {participant.user.id}"
                )
                logger.info(f"Code length: {len(code_content)} chars")

                with transaction.atomic():
                    if tasksolution:
                        # Update existing submission (overwrite)
                        tasksolution.code = code_content
                        tasksolution.attempts += 1
                        tasksolution.status = "pending"
                        tasksolution.kafka_sent_at = timezone.now()
                        tasksolution.submitted_at = timezone.now()
                        # Reset results
                        tasksolution.score = 0
                        tasksolution.is_corrected = False
                        tasksolution.passed_tests = 0
                        tasksolution.total_tests = 0
                        tasksolution.test_results = []
                        tasksolution.error_message = None
                        tasksolution.compiler_output = None
                        submission = tasksolution
                        logger.info(
                            f"Updated existing TaskSolution (ID: {submission.id}, attempts: {submission.attempts}/{max_attempts})"
                        )
                    else:
                        # Create new submission record
                        submission = TaskSolution(
                            task=task,
                            participant=participant,
                            team=participant.team,
                            code=code_content,
                            attempts=1,
                            status="pending",
                            kafka_sent_at=timezone.now(),
                        )
                        logger.info(
                            f"Creating new TaskSolution (attempt 1/{max_attempts})"
                        )

                    submission.save()
                    logger.info(f"Saved TaskSolution with ID: {submission.id}")

                    # Send to Kafka for async processing (hardcoded language_id=50 for C)
                    logger.info(f"Sending submission {submission.id} to Kafka...")
                    kafka_sent = send_submission_sync(
                        submission_id=submission.id,
                        task_id=task.id,
                        user_id=participant.user.id,
                        team_id=participant.team.id,
                        code=code_content,
                        language_id=50,  # Always use C
                    )

                    logger.info(f"Kafka send result: {kafka_sent}")

                    if kafka_sent:
                        submission.status = "processing"
                        submission.save()
                        logger.info(
                            f"✓ Submission {submission.id} sent to Kafka and status updated to 'processing'"
                        )

                        # Update context with new attempts
                        context["tasksolution"] = submission
                        context["current_attempts"] = submission.attempts
                        context["remaining_attempts"] = (
                            max_attempts - submission.attempts
                        )
                        context["can_submit"] = (
                            context["remaining_attempts"] > 0
                            and submission.status != "processing"
                        )

                        messages.success(
                            request,
                            f"Submission received! (Attempt {submission.attempts}/{max_attempts}) Your code is being evaluated...",
                        )
                    else:
                        logger.warning(
                            f"✗ Failed to send submission {submission.id} to Kafka"
                        )
                        messages.warning(
                            request,
                            "Submission saved but evaluation service is unavailable. "
                            "It will be processed when the service is back online.",
                        )

            except Exception as exp:
                logger.error(f"Error submitting code: {str(exp)}", exc_info=True)
                messages.error(request, f"Error submitting code: {str(exp)}")

        return render(request, "tasks/challenge-detailes.html", context)
    else:  # GET
        return render(request, "tasks/challenge-detailes.html", context)


@login_required
def tasksFileDownload(request: HttpRequest):
    file_path = os.path.join(settings.MEDIA_ROOT, "tasks.rar")
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True)
    raise Http404


@login_required
def leaderboardView(request: HttpRequest):
    """
    Display team leaderboard based on completed tasks.
    Score calculation: (task_score% * task_points)
    Only completed tasks count toward the total.
    Frozen during rush_hour for suspense (no data rendered for security).
    """

    # Check if rush hour is active
    settings = Settings.get_settings()
    rush_hour_active = settings.rush_hour

    # If rush hour is active, skip all database queries and render empty page
    if rush_hour_active:
        context = {
            "rush_hour_active": True,
            "top_three": [],
            "rest": [],
            "total_teams": 0,
        }
        return render(request, "tasks/leaderboard.html", context)

    # Get all teams with their completed submissions
    teams = Team.objects.all()

    leaderboard_data = []

    for team in teams:
        # Get all completed submissions for this team
        completed_submissions = TaskSolution.objects.filter(
            team=team, status="completed", is_corrected=True
        ).select_related("task")

        total_score = 0
        completed_tasks = 0
        task_details = []

        # Calculate score for each completed task
        # Group by task to get the best submission per task
        tasks_with_submissions = {}

        for submission in completed_submissions:
            task_id = submission.task.id
            if task_id not in tasks_with_submissions:
                tasks_with_submissions[task_id] = submission
            else:
                # Keep the submission with the higher score
                if submission.score > tasks_with_submissions[task_id].score:
                    tasks_with_submissions[task_id] = submission

        # Calculate total score
        for task_id, submission in tasks_with_submissions.items():
            task_points = submission.task.points
            score_percentage = submission.score / 100.0
            earned_points = score_percentage * task_points
            total_score += earned_points
            completed_tasks += 1

            task_details.append(
                {
                    "task_title": submission.task.title,
                    "task_points": task_points,
                    "score_percentage": submission.score,
                    "earned_points": earned_points,
                }
            )

        leaderboard_data.append(
            {
                "team": team,
                "total_score": round(total_score, 2),
                "completed_tasks": completed_tasks,
                "task_details": task_details,
            }
        )

    # Sort by total score descending
    leaderboard_data.sort(key=lambda x: x["total_score"], reverse=True)

    # Add rank to each team
    for idx, team_data in enumerate(leaderboard_data, start=1):
        team_data["rank"] = idx

    # Separate top 3 and rest
    top_three = leaderboard_data[:3] if len(leaderboard_data) >= 3 else leaderboard_data
    rest = leaderboard_data[3:] if len(leaderboard_data) > 3 else []

    context = {
        "top_three": top_three,
        "rest": rest,
        "total_teams": len(leaderboard_data),
        "rush_hour_active": False,
    }

    return render(request, "tasks/leaderboard.html", context)


@login_required
def shopView(request: HttpRequest):
    """
    Display shop with available powers and handle purchases.
    Teams can buy powers using coins earned from completing tasks.
    Cooldown period between purchases prevents spam.
    """
    from .models import ShopPower, TeamPurchase
    from datetime import timedelta

    # Get current user's team
    try:
        participant = Participant.objects.get(user=request.user)
        team = participant.team
    except:
        messages.error(request, "You must be part of a team to access the shop")
        return redirect("tasksDisplay")

    # Get platform settings for cooldown
    settings_obj = Settings.get_settings()
    cooldown_minutes = settings_obj.shop_cooldown_minutes

    # Check last purchase for cooldown
    last_purchase = (
        TeamPurchase.objects.filter(team=team).order_by("-purchased_at").first()
    )
    can_purchase = True
    cooldown_remaining = None

    if last_purchase:
        time_since_purchase = timezone.now() - last_purchase.purchased_at
        cooldown_period = timedelta(minutes=cooldown_minutes)

        if time_since_purchase < cooldown_period:
            can_purchase = False
            cooldown_remaining = cooldown_period - time_since_purchase

    # Get all active powers
    powers = ShopPower.objects.filter(is_active=True).order_by("cost")

    # Get team's purchase history
    purchases = (
        TeamPurchase.objects.filter(team=team)
        .select_related("power")
        .order_by("-purchased_at")
    )

    if request.method == "POST":
        power_id = request.POST.get("power_id")

        if not can_purchase:
            messages.error(
                request,
                f"You must wait {cooldown_remaining.total_seconds() // 60:.0f} more minutes before purchasing again",
            )
            return redirect("shop")

        try:
            power = ShopPower.objects.get(id=power_id, is_active=True)

            # Check if team has enough coins
            if team.coins < power.cost:
                messages.error(
                    request,
                    f"Insufficient coins! You have {team.coins} coins but need {power.cost}",
                )
                return redirect("shop")

            with transaction.atomic():
                # Deduct coins
                team.coins -= power.cost
                team.save()

                # Create purchase record
                TeamPurchase.objects.create(
                    team=team, power=power, coins_spent=power.cost
                )

                logger.info(
                    f"Team {team.name} purchased {power.name} for {power.cost} coins"
                )
                messages.success(
                    request,
                    f"Successfully purchased {power.name}! You now have {team.coins} coins remaining.",
                )

        except ShopPower.DoesNotExist:
            messages.error(request, "Power not found or no longer available")
        except Exception as e:
            logger.error(f"Error processing purchase: {str(e)}", exc_info=True)
            messages.error(request, "Error processing purchase. Please try again.")

        return redirect("shop")

    context = {
        "team": team,
        "powers": powers,
        "purchases": purchases,
        "can_purchase": can_purchase,
        "cooldown_remaining": cooldown_remaining,
        "cooldown_minutes": cooldown_minutes,
    }

    return render(request, "tasks/shop.html", context)


@login_required
def useTimeMachineView(request: HttpRequest, task_id: int):
    """
    Use Time Machine power to get one extra attempt on a task.
    Uses power handler system for flexible power logic.
    """
    from .power_handlers import get_power_handler

    if request.method != "POST":
        return redirect("task", task_id=task_id)

    try:
        participant = Participant.objects.get(user=request.user)
        team = participant.team
    except:
        messages.error(request, "You must be part of a team")
        return redirect("tasksDisplay")

    try:
        task = Task.objects.get(id=task_id)
        tasksolution = TaskSolution.objects.filter(task=task, team=team).first()

        if not tasksolution:
            messages.error(request, "No submission found for this task")
            return redirect("task", task_id=task_id)

        # Get Time Machine handler
        TimeMachine = get_power_handler("time_machine")
        if not TimeMachine:
            messages.error(request, "Time Machine power not found")
            return redirect("task", task_id=task_id)

        # Use the power
        success, message = TimeMachine.use(
            team=team, task=task, tasksolution=tasksolution
        )

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

    except Task.DoesNotExist:
        messages.error(request, "Task not found")
        return redirect("tasksDisplay")
    except Exception as e:
        logger.error(f"Error using Time Machine: {str(e)}", exc_info=True)
        messages.error(request, "Error activating Time Machine. Please try again.")

    return redirect("task", task_id=task_id)

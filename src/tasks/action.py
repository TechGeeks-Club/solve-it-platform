from django.contrib import admin
from django.contrib import messages

from .models import TaskSolution,TaskCorrecton

from django.db import transaction


@admin.action(description="Get the selected tasks")
def Get_task(modeladmin, request, queryset):
    for qs in queryset:
        if not TaskCorrecton.objects.filter(task_solution=qs).exists():
            TaskCorrecton.objects.create(task_solution=qs, user=request.user)
        else:
            messages.error(request, "This task is already taken by you or another user")

@admin.action(description="Exclude the selected tasks")
def Exclude_task(modeladmin, request, queryset):
    for qs in queryset:
        
        if TaskCorrecton.objects.filter(task_solution=qs).exists() and TaskCorrecton.objects.get(task_solution=qs).user == request.user:
            TaskCorrecton.objects.get(task_solution=qs).delete()
        else:
            messages.error(request, "This task is not taken by user")
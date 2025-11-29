from django.contrib import admin
from django.contrib.admin import ModelAdmin

from django import forms


from .models import Phase, Task, TaskTest, TaskSolution
from .forms import TaskSolutionForm

from django.contrib.admin import StackedInline,TabularInline

from .filters import TaskSolutionListFilter

from django.utils.html import format_html

class TaskSolutionStackedInline(TabularInline):
    model = TaskSolution 
    fields = ['pk','team',"participant",'score','tries']
    show_change_link = True
    readonly_fields = ['pk','team',"participant",'score','tries']
    can_delete = False
    extra = 0
    tab = True
    

@admin.register(Phase)
class PhaseAdmin(ModelAdmin):
    
    model = Phase
    list_display = ('id','name','is_locked')
    list_display_links = list_display


@admin.register(Task)
class TaskAdmin(ModelAdmin):
    
    model = Task
    list_display = ('id','_title','phase','level','category','points')
    list_display_links = list_display
    
    search_fields = ('_title',)
    list_filter = ('phase', 'level', 'category')
    
    inlines =  [TaskSolutionStackedInline]
    
    
    def _title(self, obj):
        if len(obj.title) <= 15:
            return obj.title
        return obj.title[:15] + "..."
    
    
    
@admin.register(TaskSolution)
class TaskSolutionAdmin(ModelAdmin):
    form = TaskSolutionForm
    model = TaskSolution
    
    list_display = (
        'id', 'task__phase', 'team__name', '_title', 'task__level', 'task__category',
        '_score', 'status', '_passed_tests', 'is_corrected'
    )
    list_display_links = ('id', 'task__phase', 'team__name', '_title')
    
    search_fields = ('task__title', 'team__name', "participant__user__username")
    list_filter = ('task__phase', 'status', TaskSolutionListFilter, 'is_corrected', 'task__level', 'task__category')
    
    readonly_fields = (
        'task', 'team', 'submitted_at', 'participant',
        'status', 'kafka_sent_at', 'processing_started_at', 'processing_completed_at',
        'passed_tests', 'total_tests', 'score',
        'compiler_output', 'error_message', 'test_results',
        'correction_id'
    )
    
    fieldsets = (
        ("Submission Information", {
            "fields": (("task", "submitted_at"), ("team", "participant"), "correction_id")
        }),
        ("Code Submission", {
            "fields": ("code_src", ("score", "is_corrected")),
            "classes": ["tab"],
        }),
        ("Judge0 Processing", {
            "fields": (
                "status",
                ("kafka_sent_at", "processing_started_at", "processing_completed_at"),
                ("passed_tests", "total_tests"),
            ),
            "classes": ["collapse"],
        }),
        ("Judge0 Results", {
            "fields": ("compiler_output", "error_message", "test_results"),
            "classes": ["collapse"],
        }),
    )
    

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    
    def _score(self, obj):
        return f"{obj.score}%"
    
    def _passed_tests(self, obj):
        if obj.total_tests > 0:
            return f"{obj.passed_tests}/{obj.total_tests}"
        return "-"
    _passed_tests.short_description = "Tests"
    
    def _title(self, obj):
        if len(obj.task.title) <= 15:
            return obj.task.title
        return obj.task.title[:15] + "..."


admin.site.register(TaskTest)
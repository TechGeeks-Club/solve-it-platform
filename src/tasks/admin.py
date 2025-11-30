from django.contrib import admin
from django.contrib.admin import ModelAdmin

from django import forms


from .models import Phase, Task, TaskTest, TaskSolution, Settings, ShopPower, TeamPurchase, TeamPowerUsage
from .forms import TaskSolutionForm

from django.contrib.admin import StackedInline,TabularInline

from .filters import TaskSolutionListFilter

from django.utils.html import format_html


@admin.register(Settings)
class SettingsAdmin(ModelAdmin):
    model = Settings
    list_display = ('id', 'max_attempts', 'pass_threshold', 'manual_correction', 'rush_hour', 'shop_cooldown_minutes', 'updated_at')
    
    fieldsets = (
        ("Submission Settings", {
            "fields": ("max_attempts", "pass_threshold")
        }),
        ("Correction Settings", {
            "fields": ("manual_correction",)
        }),
        ("Event Settings", {
            "fields": ("rush_hour",),
            "description": "Freeze the leaderboard during rush hour to create suspense. Teams can still submit solutions."
        }),
        ("Shop Settings", {
            "fields": ("shop_cooldown_minutes",),
            "description": "Cooldown period in minutes before teams can make another shop purchase."
        }),
        ("First Solver Bonus", {
            "fields": ("first_solver_bonus_percent",),
            "description": "Percentage bonus for the first solver of a task."
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one Settings instance
        return not Settings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of Settings
        return False


class TaskTestInline(TabularInline):
    model = TaskTest
    fields = ['input', 'output', 'display', 'weight', 'is_sample', 'order']
    extra = 1
    ordering = ['order', 'id']
    

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
    list_display = ('id','_title','phase','level','category','points','coins')
    list_display_links = list_display
    
    search_fields = ('_title',)
    list_filter = ('phase', 'level', 'category')
    
    inlines = [TaskTestInline]
    
    
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
        '_score', '_attempts', 'status', '_passed_tests', 'is_corrected'
    )
    list_display_links = ('id', 'task__phase', 'team__name', '_title')
    
    search_fields = ('task__title', 'team__name', "participant__user__username")
    list_filter = ('task__phase', 'status', TaskSolutionListFilter, 'is_corrected', 'task__level', 'task__category')
    
    def get_readonly_fields(self, request, obj=None):
        """Make score and is_corrected editable when manual_correction is enabled"""
        settings = Settings.get_settings()
        
        base_readonly = [
            'task', 'team', 'submitted_at', 'participant', 'attempts',
            'status', 'kafka_sent_at', 'processing_started_at', 'processing_completed_at',
            'passed_tests', 'total_tests',
            'compiler_output', 'error_message', 'test_results',
            'correction_id'
        ]
        
        if not settings.manual_correction:
            # If manual correction is disabled, make score and is_corrected readonly
            base_readonly.extend(['score', 'is_corrected'])
        
        return base_readonly
    
    fieldsets = (
        ("Submission Information", {
            "fields": (("task", "submitted_at"), ("team", "participant"), ("attempts", "correction_id"))
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
    
    def _attempts(self, obj):
        settings = Settings.get_settings()
        return f"{obj.attempts}/{settings.max_attempts}"
    _attempts.short_description = "Attempts"
    
    def _passed_tests(self, obj):
        if obj.total_tests > 0:
            return f"{obj.passed_tests}/{obj.total_tests}"
        return "-"
    _passed_tests.short_description = "Tests"
    
    def _title(self, obj):
        if len(obj.task.title) <= 15:
            return obj.task.title
        return obj.task.title[:15] + "..."


@admin.register(ShopPower)
class ShopPowerAdmin(ModelAdmin):
    model = ShopPower
    list_display = ('id', 'name', 'power_type', 'cost', 'is_active')
    list_display_links = ('id', 'name')
    list_filter = ('is_active', 'power_type')
    search_fields = ('name', 'description')
    
    fieldsets = (
        ("Power Information", {
            "fields": ("name", "power_type", "description", "icon")
        }),
        ("Cost & Availability", {
            "fields": ("cost", "is_active")
        }),
    )


@admin.register(TeamPurchase)
class TeamPurchaseAdmin(ModelAdmin):
    model = TeamPurchase
    list_display = ('id', 'team', 'power', 'coins_spent', 'purchased_at')
    list_display_links = ('id', 'team', 'power')
    list_filter = ('purchased_at', 'power')
    search_fields = ('team__name', 'power__name')
    readonly_fields = ('team', 'power', 'purchased_at', 'coins_spent')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(TeamPowerUsage)
class TeamPowerUsageAdmin(ModelAdmin):
    model = TeamPowerUsage
    list_display = ('id', 'team', 'power', 'task', 'used_at')
    list_display_links = ('id', 'team', 'power')
    list_filter = ('used_at', 'power')
    search_fields = ('team__name', 'power__name', 'task__title')
    readonly_fields = ('team', 'power', 'task', 'used_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
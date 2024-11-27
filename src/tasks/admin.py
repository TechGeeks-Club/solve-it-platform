from django.contrib import admin
from django.contrib.admin import ModelAdmin

from django import forms


from .models import Phase, Category, Task, TaskTest, TaskSolution
from .forms import TaskSolutionForm

from django.contrib.admin import StackedInline,TabularInline



class TaskSolutionStackedInline(TabularInline):
    model = TaskSolution 
    fields = ['pk','team',"participant",'score','tries']
    show_change_link = True
    readonly_fields = fields
    can_delete = False
    extra = 0
    tab = True
    


@admin.register(Phase)
class PhaseAdmin(ModelAdmin):
    
    model = Phase
    list_display = ('id','name','is_locked')
    list_display_links = list_display


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    
    model = Category
    list_display = ('id','name')
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
    
    list_display = ('id','task__phase','team__name','_title','task__level',"task__category",'_score','tries')
    list_display_links = list_display
    
    search_fields = ('_title',"team__name")
    list_filter = ('task__phase','task__level','task__category')
    
    # readonly_fields = ('task','team','submitted_at','tries')
    
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    
    def _score(self, obj):
        return f"{obj.score}%"
    
    def _title(self, obj):
        if len(obj.task.title) <= 15:
            return obj.task.title
        return obj.task.title[:15] + "..."
    
    
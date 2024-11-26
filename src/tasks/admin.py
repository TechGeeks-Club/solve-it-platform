from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Phase, Category, Task, TaskTest, TaskSolution


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
    
    
    def _title(self, obj):
        if len(obj.title) <= 15:
            return obj.title
        return obj.title[:15] + "..."
    
@admin.register(TaskSolution)
class TaskSolutionAdmin(ModelAdmin):
    
    model = TaskSolution
    list_display = ('id','task__phase','team__name','_title','task__level',"task__category",'_score','tries')
    list_display_links = list_display
    
    search_fields = ('_title',"team__name")
    list_filter = ('task__phase','task__level','task__category')
    
    readonly_fields = ('task','participant','team','code','submitted_at','tries')
    
    
    def _score(self, obj):
        return f"{obj.score}%"
    
    def _title(self, obj):
        if len(obj.task.title) <= 15:
            return obj.task.title
        return obj.task.title[:15] + "..."
    
    
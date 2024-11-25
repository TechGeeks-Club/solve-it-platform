from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Phase, Category, Task, TaskTest, TaskSolution

admin.site.register(Phase)
admin.site.register(Category)
# admin.site.register(Task)
admin.site.register(TaskTest)
# admin.site.register(TaskSolution)

@admin.register(Task)
class TaskAdmin(ModelAdmin):
    
    model = Task
    list_display = ('_title','phase','level','category','points')
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
    list_display = ('task__phase','team__name','_title','task__level',"task__category",'score','tries')
    list_display_links = list_display
    
    search_fields = ('_title',"team__name")
    list_filter = ('task__phase','task__level','task__category')
    
    
    def _title(self, obj):
        if len(obj.task.title) <= 15:
            return obj.task.title
        return obj.task.title[:15] + "..."
    
    
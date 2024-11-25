from django.contrib import admin
from .models import Phase, Category, Task, TaskTest, TaskSolution

admin.site.register(Phase)
admin.site.register(Category)
admin.site.register(Task)
admin.site.register(TaskTest)
admin.site.register(TaskSolution)
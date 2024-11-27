from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import F, Sum

from django.contrib.auth.models import User

from .models import Team,Participant
from tasks.models import TaskSolution

from django.contrib.admin import StackedInline,TabularInline



class ParticipantStackedInline(TabularInline):
    model = Participant 
    extra = 1
    tab = True
    


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    
    model = Team
    list_display = ("id",'name',"members_num","submeted_taskes","team_score")
    list_display_links = list_display

    inlines = [ParticipantStackedInline,]

    
    def members_num(self, obj):
        return f"{obj.participant_set.count()} / 4" #participant_set : this is reverce FK
    
    def submeted_taskes(self, obj):
        return obj.tasksolution_set.count()

    def team_score(self, obj):
        """
        Calculate and display the total score for a team in the admin panel.
        """
        total_score = TaskSolution.objects.filter(team=obj).annotate(
            task_points_score=F('task__points') * F('score') / 100
        ).aggregate(total_score=Sum('task_points_score'))['total_score']
        
        return total_score or 0
    
    
@admin.register(Participant)
class ParticipantAdmin(ModelAdmin):
    
    model = Participant
    list_display = ("id",'user__first_name','user__last_name','team__name')
    list_display_links = list_display
    
    search_fields = ('team__name','user__first_name','user__last_name')
    list_filter = ('team__name',)
    
  

  
 
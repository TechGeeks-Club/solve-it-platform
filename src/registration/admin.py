from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import Sum


from .models import Team,Participant
from tasks.models import TaskSolution


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    
    model = Team
    list_display = ("id",'name',"members_num","submeted_taskes","team_score")
    list_display_links = list_display

    def members_num(self, obj):
        return f"{obj.participant_set.count()} / 4" #participant_set : this is reverce FK
    
    def submeted_taskes(self, obj):
        return obj.tasksolution_set.count()

    def team_score(self,obj):
        return obj.tasksolution_set.aggregate(total_score=Sum('score'))["total_score"] or 0
@admin.register(Participant)
class ParticipantAdmin(ModelAdmin):
    
    model = Participant
    list_display = ("id",'user__first_name','user__last_name','team__name')
    list_display_links = list_display
    
    search_fields = ('team__name','user__first_name','user__last_name')
    list_filter = ('team__name',)
    
 
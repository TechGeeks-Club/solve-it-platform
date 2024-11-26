from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Team,Participant

admin.site.register(Team)
# admin.site.register(Participant)

class ParticipantAdmin(ModelAdmin):
    
    model = Participant
    list_display = ('name')
    list_display_links = list_display
    
    search_fields = ('_title',)
    list_filter = ('phase', 'level', 'category')
    
    
    def _title(self, obj):
        if len(obj.title) <= 15:
            return obj.title
        return obj.title[:15] + "..."
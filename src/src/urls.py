from django.contrib import admin
from django.urls import path

from registration.views import createTeamView, createParticipantView, participantLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('create_team', createTeamView,name="createTeam"),
    path('create_participant', createParticipantView,name="createParticipant"),
    path('participant_login', participantLoginView,name="participantLogin"),
]

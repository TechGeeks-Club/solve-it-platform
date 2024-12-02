from django.contrib import admin
from django.urls import path,include
from django.shortcuts import render


from registration.views import createTeamView, createParticipantView, participantLoginView ,logoutview
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: render(request, "home/home-page.html"), name="home"),
    path('create_team', createTeamView,name="createTeam"),
    path('create_participant', createParticipantView,name="createParticipant"),
    path('login', participantLoginView,name="participantLogin"),
    path('logout', logoutview,name="logout"),
 
    path('task/', include('tasks.urls')), 
]

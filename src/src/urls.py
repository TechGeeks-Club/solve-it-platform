from django.contrib import admin
from django.urls import path,include
from django.shortcuts import render, redirect


from registration.views import createTeamView, createParticipantView, participantLoginView ,logoutview

from django.conf import settings
from django.conf.urls.static import static

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('tasksDisplay')
    return render(request, "home/home-page.html")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name="home"),
    path('create_team', createTeamView,name="createTeam"),
    path('create_participant', createParticipantView,name="createParticipant"),
    path('login', participantLoginView,name="login"),
    path('logout', logoutview,name="logout"),
 
    path('task/', include('tasks.urls')), 
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
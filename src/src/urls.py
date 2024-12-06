from django.contrib import admin
from django.urls import path,include
from django.shortcuts import render


from registration.views import createTeamView, createParticipantView, participantLoginView ,logoutview

from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: render(request, "home/home-page.html"), name="home"),
    path('create_team', createTeamView,name="createTeam"),
    path('create_participant', createParticipantView,name="createParticipant"),
    path('login', participantLoginView,name="login"),
    path('logout', logoutview,name="logout"),
 
    path('task/', include('tasks.urls')), 
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
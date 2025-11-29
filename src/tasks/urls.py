from django.contrib import admin
from django.urls import path,include
from django.shortcuts import render


from .views import tasksDisplayView, taskView, tasksFileDownload, leaderboardView

urlpatterns = [
    path('display', tasksDisplayView, name="tasksDisplay"),
    path('leaderboard', leaderboardView, name="leaderboard"),
    path("<int:task_id>", taskView, name="task"),
    # path("thirdPhase", thirdPhaseView, name="thirdPhase"),
    path("tasksFile", tasksFileDownload, name="tasksFile"),
]
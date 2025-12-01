from django.urls import path


from .views import (
    tasksDisplayView,
    taskView,
    tasksFileDownload,
    leaderboardView,
    shopView,
    useTimeMachineView,
)

urlpatterns = [
    path("", tasksDisplayView, name="tasksDisplay"),
    path("leaderboard", leaderboardView, name="leaderboard"),
    path("shop", shopView, name="shop"),
    path("<int:task_id>", taskView, name="task"),
    path("<int:task_id>/use-time-machine", useTimeMachineView, name="use_time_machine"),
    path("tasksFile", tasksFileDownload, name="tasksFile"),
]

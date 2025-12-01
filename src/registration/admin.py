from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import F, Sum


from .models import Team, Participant
from tasks.models import TaskSolution

from django.contrib.admin import TabularInline


class ParticipantStackedInline(TabularInline):
    model = Participant
    fields = ["pk", "user", "first_name", "last_name", "submit", "personal_score"]

    readonly_fields = fields

    extra = 0
    tab = True

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

    def submit(self, obj):
        # the numbers of task submitted by the participant
        return obj.tasksolution_set.count()

    def personal_score(self, obj):
        # the total score of the participant
        return obj.tasksolution_set.annotate(
            task_points_score=F("task__points") * F("score") / 100
        ).aggregate(total_score=Sum("task_points_score"))["total_score"]


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    model = Team
    list_display = ("id", "name", "members_num", "submeted_taskes", "team_score")
    list_display_links = list_display

    inlines = [
        ParticipantStackedInline,
    ]

    def members_num(self, obj):
        return (
            f"{obj.participant_set.count()} / 4"  # participant_set : this is reverce FK
        )

    def submeted_taskes(self, obj):
        return obj.tasksolution_set.count()

    def team_score(self, obj):
        """
        Calculate and display the total score for a team in the admin panel.
        """
        total_score = (
            TaskSolution.objects.filter(team=obj)
            .annotate(task_points_score=F("task__points") * F("score") / 100)
            .aggregate(total_score=Sum("task_points_score"))["total_score"]
        )

        return total_score or 0


@admin.register(Participant)
class ParticipantAdmin(ModelAdmin):
    model = Participant
    list_display = (
        "id",
        "user__first_name",
        "user__last_name",
        "team__name",
        "submit",
        "personal_score",
    )
    list_display_links = list_display

    search_fields = ("team__name", "user__first_name", "user__last_name")
    list_filter = ("team__name",)

    def submit(self, obj):
        # the numbers of task submitted by the participant
        return obj.tasksolution_set.count()

    def personal_score(self, obj):
        # the total score of the participant
        return obj.tasksolution_set.annotate(
            task_points_score=F("task__points") * F("score") / 100
        ).aggregate(total_score=Sum("task_points_score"))["total_score"]

from django.db import models
from django.core.cache import cache
from registration.models import Participant, Team
from django.core.validators import MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from django.conf import settings



class Settings(models.Model):
    first_solver_bonus_percent = models.IntegerField(
        default=20,
        validators=[MaxValueValidator(100)],
        help_text="Percentage bonus for the first solver of a task.",
    )
    """Global platform settings with Redis caching"""

    max_attempts = models.IntegerField(
        default=3, help_text="Maximum number of submission attempts allowed per task"
    )
    pass_threshold = models.IntegerField(
        default=50,
        validators=[MaxValueValidator(100)],
        help_text="Minimum score percentage to consider a task as passed (e.g., 50 means 50%)",
    )
    manual_correction = models.BooleanField(
        default=False,
        help_text="Enable manual correction by admins (allows editing score and is_corrected)",
    )
    rush_hour = models.BooleanField(
        default=False,
        help_text="Freeze leaderboard during rush hour to build suspense (teams can still submit)",
    )
    shop_cooldown_minutes = models.IntegerField(
        default=60,
        help_text="Cooldown period in minutes before a team can make another shop purchase",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"

    def save(self, *args, **kwargs):
        # Ensure only one Settings instance exists
        if not self.pk and Settings.objects.exists():
            raise ValueError(
                "Settings instance already exists. Update the existing one."
            )
        super().save(*args, **kwargs)

        cache.delete(settings.CACHE_PLATFORM_SETTINGS_KEY)

    @classmethod
    def get_settings(cls):
        """Get settings from cache or database"""
        settings = cache.get(settings.CACHE_PLATFORM_SETTINGS_KEY)
        if settings is None:
            settings, _ = cls.objects.get_or_create(pk=1)
            cache.set(settings.CACHE_PLATFORM_SETTINGS_KCACHE_PLATFORM_SETTINGS_KEYEY, settings)
        return settings

    def __str__(self):
        return f"Platform Settings (max_attempts: {self.max_attempts}, pass_threshold: {self.pass_threshold}%, manual_correction: {self.manual_correction}, rush_hour: {self.rush_hour})"


class Phase(models.Model):
    name = models.CharField(max_length=128)
    is_locked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update unlocked phase IDs cache after save
        from django.core.cache import cache
        unlocked_phase_ids = list(Phase.objects.filter(is_locked=False).values_list('id', flat=True))
        cache.set(settings.CACHE_UNLOCKED_PHASE_IDS_KEY, unlocked_phase_ids)

    def __str__(self):
        return self.name


# Optionally, also update cache on delete
@receiver(post_delete, sender=Phase)
def update_unlocked_phase_ids_on_delete(sender, instance, **kwargs):
    from django.core.cache import cache
    unlocked_phase_ids = list(Phase.objects.filter(is_locked=False).values_list('id', flat=True))
    cache.set(settings.CACHE_UNLOCKED_PHASE_IDS_KEY, unlocked_phase_ids)


class Task(models.Model):
    LEVELS = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    CATEGORIES = [
        ("algorithms", "Algorithms"),
        ("data_structures", "Data Structures"),
        ("dynamic_programming", "Dynamic Programming"),
        ("graph_theory", "Graph Theory"),
        ("string_manipulation", "String Manipulation"),
        ("mathematics", "Mathematics"),
        ("greedy", "Greedy"),
        ("sorting", "Sorting"),
        ("searching", "Searching"),
        ("other", "Other"),
    ]

    phase = models.ForeignKey(
        Phase, null=True, on_delete=models.SET_NULL, related_name="phase_tasks"
    )
    category = models.CharField(
        max_length=50, choices=CATEGORIES, null=True, blank=True
    )
    title = models.CharField(max_length=128, null=False)
    context = models.TextField(null=False)
    initialCode = models.TextField(null=True)
    level = models.CharField(max_length=8, choices=LEVELS, null=True, blank=True)
    points = models.IntegerField(null=False)
    coins = models.IntegerField(
        default=1, help_text="Coins awarded for completing this task with 100% score"
    )

    nextTask = models.OneToOneField(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
    openCode = models.CharField(max_length=255, null=True, unique=True, blank=True)

    def __str__(self):
        return self.title


class TaskTest(models.Model):
    task = models.ForeignKey(
        Task, null=False, on_delete=models.CASCADE, related_name="task_tests"
    )
    input = models.TextField(null=False, blank=True)
    output = models.TextField(null=False)
    display = models.BooleanField(default=False)
    weight = models.IntegerField(default=1)  # For weighted scoring
    is_sample = models.BooleanField(default=False)  # Mark sample test cases
    order = models.IntegerField(default=0)  # Test execution order

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.task.title} - Test {self.id}"


def get_file_path(participant, filename):
    _ = filename.split(".")[-1]

    return f"upload/{participant.team.name}/{filename}_{participant.id}.c"


class TaskSolution(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    task = models.ForeignKey(
        Task, null=False, on_delete=models.CASCADE, related_name="task_solutions"
    )
    participant = models.ForeignKey(Participant, null=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(Team, null=False, on_delete=models.CASCADE)
    code = models.TextField(null=True, blank=True)  # Store code as text
    code_file = models.FileField(
        upload_to=get_file_path, blank=True, null=True, max_length=100
    )  # Optional file upload

    attempts = models.IntegerField(default=1)  # Number of attempts made
    is_corrected = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    score = models.IntegerField(
        null=True, default=0, validators=[MaxValueValidator(200)]
    )  # can be more  than 100 in case of first solver bonus
    tries = models.IntegerField(
        null=False, default=1, validators=[MaxValueValidator(3)]
    )

    # Judge0 Integration Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    kafka_sent_at = models.DateTimeField(null=True, blank=True)  # When sent to Kafka
    processing_started_at = models.DateTimeField(
        null=True, blank=True
    )  # When judge service started
    processing_completed_at = models.DateTimeField(
        null=True, blank=True
    )  # When judge service completed

    execution_time = models.FloatField(
        null=True, blank=True
    )  # Average execution time in seconds
    memory_used = models.FloatField(null=True, blank=True)  # Average memory in KB
    compiler_output = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)  # Runtime errors

    passed_tests = models.IntegerField(default=0)
    total_tests = models.IntegerField(default=0)
    test_results = models.JSONField(
        null=True, blank=True, default=list
    )  # Detailed results per test (includes execution_time and memory_usage per test)
    correction_id = models.CharField(
        max_length=255, null=True, blank=True
    )  # Unique identifier for this correction

    def save(self, *args, **kwargs):
        if self.score and self.score > 0:
            self.is_corrected = True
        super().save(*args, **kwargs)

    def calculate_score(self):
        """Calculate score based on passed tests"""
        if self.total_tests > 0:
            return int((self.passed_tests / self.total_tests) * 100)
        return 0

    def is_passed(self):
        """Check if task is passed based on threshold and max attempts"""
        settings = Settings.get_settings()
        # Only consider passed if max attempts reached and score >= threshold
        if self.attempts >= settings.max_attempts:
            return self.score >= settings.pass_threshold
        return None  # Still in progress

    def get_status_display_text(self):
        """Get status text for display (Success/Failed/In Progress)"""
        settings = Settings.get_settings()
        if self.attempts >= settings.max_attempts:
            return "Success" if self.score >= settings.pass_threshold else "Failed"
        return "In Progress"

    def get_status_class(self):
        """Get CSS class for status styling"""
        settings = Settings.get_settings()
        if self.attempts >= settings.max_attempts:
            return "success" if self.score >= settings.pass_threshold else "failed"
        return "in-progress"

    def __str__(self):
        return f"{self.task.title} - Solution #{self.tries} by {self.participant}"


class ShopPower(models.Model):
    """Available powers in the shop"""

    POWER_TYPES = [
        ("time_machine", "Time Machine"),
    ]

    name = models.CharField(max_length=100)
    power_type = models.CharField(max_length=50, choices=POWER_TYPES, unique=True)
    description = models.TextField()
    cost = models.IntegerField(help_text="Cost in coins")
    is_active = models.BooleanField(default=True)
    icon = models.TextField(default="⏰", help_text="SVG icon or emoji for display")

    def __str__(self):
        return f"{self.name} ({self.cost} coins)"


class TeamPurchase(models.Model):
    """Track team purchases and cooldowns"""

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="purchases")
    power = models.ForeignKey(ShopPower, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    coins_spent = models.IntegerField()

    class Meta:
        ordering = ["-purchased_at"]

    def __str__(self):
        return f"{self.team.name} - {self.power.name} at {self.purchased_at}"


class TeamPowerUsage(models.Model):
    """Track when teams use their purchased powers"""

    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="power_usages"
    )
    power = models.ForeignKey(ShopPower, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-used_at"]

    def __str__(self):
        return f"{self.team.name} used {self.power.name} on {self.task.title if self.task else 'N/A'}"

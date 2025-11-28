from django.db import models

from registration.models import Participant, Team
from django.core.validators import MaxValueValidator

from django.contrib.auth.models import User

class Phase(models.Model):
    name = models.CharField(max_length=128)
    is_locked = models.BooleanField(default=False)

    #  update function
    
    def save(self, *args, **kwargs):
        if not self.is_locked:
            Phase.objects.all().update(is_locked=True)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class Task(models.Model):
    LEVELS = [
        ("easy","Easy"),
        ("medium","Medium"),
        ("hard","Hard"),
    ]
    phase = models.ForeignKey(Phase, null=True, on_delete=models.SET_NULL, related_name="phase_tasks")
    category = models.ForeignKey(Category, null=True,blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=128,null=False)
    context = models.TextField(null=False)
    initialCode = models.TextField(null=True)
    level = models.CharField(max_length=8, choices=LEVELS, null=True,blank=True)
    points = models.IntegerField(null=False)

    nextTask = models.OneToOneField("self", on_delete=models.SET_NULL, null=True, blank=True)
    openCode = models.CharField(max_length=255, null=True ,unique=True, blank=True)
    

    def __str__(self):
        return self.title
    

class TaskTest(models.Model):
    task = models.ForeignKey(Task, null=False, on_delete=models.CASCADE, related_name="task_tests")
    input = models.TextField(null=False, blank=True)
    output = models.TextField(null=False)
    display = models.BooleanField(default=False)
    weight = models.IntegerField(default=1)  # For weighted scoring
    is_sample = models.BooleanField(default=False)  # Mark sample test cases
    order = models.IntegerField(default=0)  # Test execution order
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.task.title} - Test {self.id}"




def get_file_path(participant, filename):
    _ = filename.split('.')[-1]
    
    return f'upload/{participant.team.name}/{filename}_{participant.id}.c'

class TaskSolution(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    task = models.ForeignKey(Task, null=False, on_delete=models.CASCADE, related_name="task_solutions")
    participant = models.ForeignKey(Participant, null=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(Team, null=False, on_delete=models.CASCADE)
    code = models.TextField(null=True, blank=True)  # Store code as text
    code_file = models.FileField(upload_to=get_file_path, blank=True, null=True, max_length=100)  # Optional file upload
    language_id = models.IntegerField(default=50)  # Judge0 language ID (50 = C)
    
    is_corrected = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    score = models.IntegerField(null=True, default=0, validators=[MaxValueValidator(100)])
    tries = models.IntegerField(null=False, default=1, validators=[MaxValueValidator(3)])
    
    # Judge0 Integration Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    kafka_sent_at = models.DateTimeField(null=True, blank=True)  # When sent to Kafka
    processing_started_at = models.DateTimeField(null=True, blank=True)  # When judge service started
    processing_completed_at = models.DateTimeField(null=True, blank=True)  # When judge service completed
    
    execution_time = models.FloatField(null=True, blank=True)  # Average execution time in seconds
    memory_used = models.FloatField(null=True, blank=True)  # Average memory in KB
    compiler_output = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)  # Runtime errors
    
    passed_tests = models.IntegerField(default=0)
    total_tests = models.IntegerField(default=0)
    test_results = models.JSONField(null=True, blank=True, default=list)  # Detailed results per test
            
    def save(self, *args, **kwargs):
        if self.score and self.score > 0:
            self.is_corrected = True
        super().save(*args, **kwargs)
    
    def calculate_score(self):
        """Calculate score based on passed tests"""
        if self.total_tests > 0:
            return int((self.passed_tests / self.total_tests) * 100)
        return 0

    def __str__(self):
        return f"{self.task.title} - Solution #{self.tries} by {self.participant}" 

class TaskCorrecton(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    task_solution = models.ForeignKey(TaskSolution, null=False, on_delete=models.CASCADE)
    corrected_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    
    def __str__(self):
        return self.task_solution.task.title
    
    class meta:
        unique_together = ('user', 'task_solution')



class ThirdPhaseCode(models.Model):
    RESULT = [
        ("win","Win"),
        ("lose","Lose"),
    ]
    # ? Which it's the code
    id = models.CharField( max_length=255, primary_key=True, unique=True,)
    task = models.ForeignKey(Task, null=False, on_delete=models.CASCADE)
    hints_value = models.IntegerField(null=False, default=1)
    result = models.CharField(max_length=8, choices=RESULT, null=False)

    def __str__(self):
        return "task: " + self.task.title + " result: " + self.result + " code: " + self.id 
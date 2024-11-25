from django.db import models

from registration.models import Participant, Team
from django.core.validators import MaxValueValidator

class Phase(models.Model):
    name = models.TextField(null=False)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.TextField(null=False)

    def __str__(self):
        return self.name
    

class Task(models.Model):
    LEVELS = [
        ("easy","Easy"),
        ("medium","Medium"),
        ("hard","Hard"),
    ]
    phase = models.ForeignKey(Phase, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=128,null=False)
    context = models.TextField(null=False)
    level = models.CharField(max_length=8, choices=LEVELS, null=False)
    points = models.IntegerField(null=False)

    def __str__(self):
        return self.title
    

class TaskTest(models.Model):
    task = models.ForeignKey(Task, null=False, on_delete=models.CASCADE)
    input = models.TextField(null=False)
    output = models.TextField(null=False)
    
    def __str__(self):
        return self.task.title + " tests"




def get_file_path(participant, filename):
    file_extention = filename.split('.')[-1]
    
    return f'upload/{participant.team.name}/{filename}_{participant.id}.c'

class TaskSolution(models.Model):
    task = models.ForeignKey(Task, null=False, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, null=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(Team, null=False, on_delete=models.CASCADE)
    code = models.FileField(upload_to=get_file_path, blank=True, max_length=100)
    score = models.IntegerField(null=False)
    tries = models.IntegerField(null=False, default=0, validators=[MaxValueValidator(3)] )
    
    def __str__(self):
        return self.task.title + " tests"

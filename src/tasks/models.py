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
    input = models.TextField(null=False)
    output = models.TextField(null=False)
    display = models.BooleanField(default=False)
    
    def __str__(self):
        return self.task.title + " tests"




def get_file_path(participant, filename):
    _ = filename.split('.')[-1]
    
    return f'upload/{participant.team.name}/{filename}_{participant.id}.c'

class TaskSolution(models.Model):
    task = models.ForeignKey(Task, null=False, on_delete=models.CASCADE, related_name="task_solutions")
    participant = models.ForeignKey(Participant, null=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(Team, null=False, on_delete=models.CASCADE)
    
    # code = models.FileField(upload_to=get_file_path, blank=True, max_length=100)
    code = models.TextField(null=False,blank=False)
    
    is_corrected = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    score = models.IntegerField(null=True, default=0, validators=[MaxValueValidator(100)] )
    # ? i change the default here to 1 bcz we create obj form this class in the first solution so first try 
    tries = models.IntegerField(null=False, default=1, validators=[MaxValueValidator(3)] )
            
    def save(self):
        if self.score > 0:
            self.is_corrected = True
        super().save()

    def __str__(self):
        return self.task.title + " Solution n"+ str(self.tries) 

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
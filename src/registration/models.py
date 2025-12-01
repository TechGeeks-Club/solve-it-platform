from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


class Team(models.Model):
    name = models.CharField(max_length=70, unique=True)
    password = models.CharField(
        max_length=255
    )  # ? to make sure that the size will fit the hashed password
    coins = models.IntegerField(
        default=0, help_text="Team's coin balance for shop purchases"
    )

    def save(self, *args, **kwargs):
        if self.password:
            self.password = make_password(self.password)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.username

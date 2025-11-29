from django.contrib import admin
from django.contrib import messages

from .models import TaskSolution

from django.db import transaction

# Manual correction tracking actions removed - now using automated Judge0 scoring
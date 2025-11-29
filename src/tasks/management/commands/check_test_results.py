from django.core.management.base import BaseCommand
from tasks.models import TaskSolution
import json


class Command(BaseCommand):
    help = 'Check test results structure'

    def handle(self, *args, **options):
        submissions = TaskSolution.objects.filter(test_results__isnull=False).order_by('-id')[:3]
        
        if not submissions.exists():
            self.stdout.write(self.style.WARNING('No submissions with test results found'))
            return
        
        for submission in submissions:
            self.stdout.write(self.style.SUCCESS(f'\n=== Submission ID: {submission.id} ==='))
            self.stdout.write(f'Task: {submission.task.title}')
            self.stdout.write(f'Number of test results: {len(submission.test_results)}')
            
            for idx, test in enumerate(submission.test_results):
                self.stdout.write(f'\nTest {idx + 1}:')
                self.stdout.write(f'  Passed: {test.get("passed")}')
                self.stdout.write(f'  Display: {test.get("display")}')
                self.stdout.write(f'  Has input: {"input" in test}')
                self.stdout.write(f'  Has expected_output: {"expected_output" in test}')

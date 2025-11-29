from django.core.management.base import BaseCommand
from tasks.models import TaskSolution, TaskTest


class Command(BaseCommand):
    help = 'Enrich existing test results with display flags and test data'

    def handle(self, *args, **options):
        submissions = TaskSolution.objects.filter(
            test_results__isnull=False,
            is_corrected=True
        ).select_related('task')
        
        updated_count = 0
        
        for submission in submissions:
            # Get task tests with display flags
            task_tests = list(
                TaskTest.objects.filter(task=submission.task)
                .order_by('order', 'id')
                .values('id', 'display', 'input', 'output')
            )
            
            if not task_tests:
                continue
            
            # Enrich test results
            enriched_results = []
            for idx, test_result in enumerate(submission.test_results):
                enriched_test = test_result.copy()
                if idx < len(task_tests):
                    enriched_test['display'] = task_tests[idx]['display']
                    enriched_test['input'] = task_tests[idx]['input']
                    enriched_test['expected_output'] = task_tests[idx]['output']
                else:
                    enriched_test['display'] = False
                enriched_results.append(enriched_test)
            
            # Update submission
            submission.test_results = enriched_results
            submission.save(update_fields=['test_results'])
            updated_count += 1
            
            if updated_count % 10 == 0:
                self.stdout.write(f'Updated {updated_count} submissions...')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully enriched {updated_count} submissions')
        )

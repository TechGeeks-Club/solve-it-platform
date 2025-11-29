from django.core.management.base import BaseCommand
from tasks.models import TaskSolution, Settings


class Command(BaseCommand):
    help = 'Fix submission status based on score and pass threshold'

    def handle(self, *args, **options):
        settings = Settings.get_settings()
        threshold = settings.pass_threshold
        
        # Get all corrected submissions
        submissions = TaskSolution.objects.filter(is_corrected=True).exclude(status='processing')
        
        updated_count = 0
        for submission in submissions:
            old_status = submission.status
            
            # Determine correct status based on score and threshold
            if submission.score >= threshold:
                new_status = 'completed'
            else:
                new_status = 'failed'
            
            # Update if different
            if old_status != new_status:
                submission.status = new_status
                submission.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated submission {submission.id}: {old_status} -> {new_status} '
                        f'(score: {submission.score}%, threshold: {threshold}%)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully updated {updated_count} submissions based on threshold {threshold}%'
            )
        )

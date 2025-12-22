import os
from django.core.management.base import BaseCommand
from django.conf import settings
from assessment_flow.models import AssessmentOption

class Command(BaseCommand):
    help = 'Exports all unique Arabic response texts to a text file for translation'

    def handle(self, *args, **options):
        # Get all unique text_ar values, excluding empty ones
        responses = AssessmentOption.objects.exclude(text_ar__exact='').values_list('text_ar', flat=True).distinct()
        
        file_path = os.path.join(settings.BASE_DIR, 'responses_to_translate.txt')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for text in responses:
                f.write(f"{text}\n")
        
        self.stdout.write(self.style.SUCCESS(f"Successfully exported {len(responses)} unique responses to {file_path}"))

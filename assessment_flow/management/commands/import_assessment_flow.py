import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from assessment_flow.models import AssessmentQuestion, AssessmentOption

class Command(BaseCommand):
    help = 'Imports assessment questions and options from a JSON file, preserving IDs'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'assessment_flow.json')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Clear existing data
        self.stdout.write('Deleting existing assessment questions...')
        AssessmentQuestion.objects.all().delete()

        # Create Questions and Options
        for item in data:
            json_id = item['id']
            text = item['text']
            option_type_str = item['option_type']
            
            # Map option type
            option_type = AssessmentQuestion.OptionType.STATIC
            if option_type_str == 'DYNAMIC_SURVEY_QUESTIONS':
                option_type = AssessmentQuestion.OptionType.DYNAMIC_SURVEY_QUESTIONS
            elif option_type_str == 'DYNAMIC_FROM_PREVIOUS_MULTI_SELECT':
                option_type = AssessmentQuestion.OptionType.DYNAMIC_FROM_PREVIOUS_MULTI_SELECT
            elif option_type_str == 'INDICATOR_LIST':
                option_type = AssessmentQuestion.OptionType.INDICATOR_LIST

            # Explicitly set the ID
            question = AssessmentQuestion.objects.create(
                id=json_id,
                text_ar=text, 
                text_en=text, # Fallback
                option_type=option_type
            )
            
            self.stdout.write(f"Created Question ID {question.id}: {text[:30]}...")

            for response in item.get('responses', []):
                resp_text = response['text']
                
                response_type = AssessmentOption.ResponseType.PREDEFINED
                if "(إدخال نص حر)" in resp_text:
                    response_type = AssessmentOption.ResponseType.FREE_TEXT
                    resp_text = "" 
                elif "(إدخال رابط)" in resp_text:
                    response_type = AssessmentOption.ResponseType.URL
                    resp_text = ""

                AssessmentOption.objects.create(
                    question=question,
                    text_ar=resp_text,
                    text_en=resp_text,
                    response_type=response_type
                )

        self.stdout.write(self.style.SUCCESS('Successfully imported assessment questions and options with preserved IDs'))

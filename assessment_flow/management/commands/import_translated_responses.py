import os
from django.core.management.base import BaseCommand
from django.conf import settings
from assessment_flow.models import AssessmentOption

class Command(BaseCommand):
    help = 'Imports English translations for assessment responses'

    def handle(self, *args, **options):
        ar_file_path = os.path.join(settings.BASE_DIR, 'responses_to_translate.txt')
        en_file_path = os.path.join(settings.BASE_DIR, 'responses_to_translate_EN.txt')
        
        if not os.path.exists(ar_file_path):
            self.stdout.write(self.style.ERROR(f'Arabic file not found: {ar_file_path}'))
            return
            
        if not os.path.exists(en_file_path):
            self.stdout.write(self.style.ERROR(f'English file not found: {en_file_path}'))
            return

        with open(ar_file_path, 'r', encoding='utf-8') as f_ar:
            ar_lines = [line.strip() for line in f_ar.readlines()]
            
        with open(en_file_path, 'r', encoding='utf-8') as f_en:
            en_lines = [line.strip() for line in f_en.readlines()]
            
        if len(ar_lines) != len(en_lines):
            self.stdout.write(self.style.ERROR(f'Line count mismatch: Arabic ({len(ar_lines)}) vs English ({len(en_lines)})'))
            return
            
        translation_map = dict(zip(ar_lines, en_lines))
        
        updated_count = 0
        options = AssessmentOption.objects.all()
        
        for option in options:
            if option.text_ar in translation_map:
                option.text_en = translation_map[option.text_ar]
                option.save()
                updated_count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} assessment options with English translations'))

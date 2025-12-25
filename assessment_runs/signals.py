from django.db.models.signals import post_save
from django.dispatch import receiver
from surveys.models import SurveyVersion
from .models import AssessmentRun

@receiver(post_save, sender=SurveyVersion)
def create_assessment_run(sender, instance, created, **kwargs):
    if created:
        AssessmentRun.objects.create(survey_version=instance)

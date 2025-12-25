from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from .models import SurveyQuestion, SurveyVersion
from Rbank.models import ResponseGroup
from Qbank.models import MatrixItemGroup


def survey_builder(request):
    available_questions_qs = (
        SurveyQuestion.objects.select_related("survey_version")
        .exclude(survey_version__status=SurveyVersion.Status.ARCHIVED)
        .only("id", "text_ar", "text_en", "code", "created_at", "survey_version__status")
        .order_by("-created_at")
    )
    available_questions = [
        {
            "id": question.id,
            "label": question.display_text,
            "code": question.code,
            "created_at": question.created_at.isoformat(),
        }
        for question in available_questions_qs
    ]

    response_types = [
        {"value": choice.value, "label": choice.label}
        for choice in SurveyQuestion.ResponseType
    ]

    response_groups = [
        {"value": rg.id, "label": rg.name}
        for rg in ResponseGroup.objects.all()
    ]

    matrix_item_groups = [
        {"value": mig.id, "label": mig.name}
        for mig in MatrixItemGroup.objects.all()
    ]

    survey_versions = SurveyVersion.objects.select_related('survey').prefetch_related('questions').all()
    version_choices = [
        {
            "id": version.id,
            "label": f"{version.survey.display_name} - {version.version_label}"
        }
        for version in survey_versions
    ]

    survey_structures = {}
    for version in survey_versions:
        sections = {}
        for q in version.questions.all():
            # Use a default section title if none is provided
            section_title = q.section_label or _("قسم غير مسمى")
            if section_title not in sections:
                sections[section_title] = {
                    "title": section_title,
                    "description": "",  # No description field on section, can be added if needed
                    "questions": []
                }
            
            # Append question data
            sections[section_title]["questions"].append({
                "question_id": q.id,
                "required": q.is_required,
                # Add other relevant fields here if needed for the builder
            })
        survey_structures[version.id] = list(sections.values())

    return render(
        request,
        "surveys/builder.html",
        {
            "available_questions": available_questions,
            "response_types": response_types,
            "response_groups": response_groups,
            "matrix_item_groups": matrix_item_groups,
            "survey_versions": version_choices,
            "survey_structures": survey_structures,
        },
    )

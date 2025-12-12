from django.shortcuts import render

from .models import SurveyQuestion


def survey_builder(request):
    response_types = []
    feature_map = {
        SurveyQuestion.ResponseType.BINARY: {
            "supports_options": True,
            "description": "Quick yes/no with predefined options.",
        },
        SurveyQuestion.ResponseType.SINGLE_CHOICE: {
            "supports_options": True,
            "description": "Pick one option from a list.",
        },
        SurveyQuestion.ResponseType.MULTIPLE_CHOICE: {
            "supports_options": True,
            "description": "Pick many options from a list.",
        },
        SurveyQuestion.ResponseType.FREE_TEXT: {
            "supports_options": False,
            "description": "Let respondents answer in their own words.",
        },
        SurveyQuestion.ResponseType.NUMERIC: {
            "supports_options": False,
            "description": "Capture counts or continuous values.",
        },
        SurveyQuestion.ResponseType.DATE: {
            "supports_options": False,
            "description": "Ask for a calendar date.",
        },
        SurveyQuestion.ResponseType.DATETIME: {
            "supports_options": False,
            "description": "Date and time together.",
        },
        SurveyQuestion.ResponseType.SCALE: {
            "supports_options": False,
            "description": "Ratings such as 1–5 agreement scales.",
        },
        SurveyQuestion.ResponseType.MATRIX: {
            "supports_options": True,
            "supports_matrix": True,
            "description": "Grid of rows and columns scored with shared options.",
        },
    }

    for value, label in SurveyQuestion.ResponseType.choices:
        response_types.append(
            {
                "value": value,
                "label": label,
                **feature_map.get(value, {}),
            }
        )

    sample_sections = [
        {
            "title": "Profile",
            "description": "Baseline attributes to segment respondents.",
            "questions": [
                {
                    "text": "What best describes your role?",
                    "response_type": SurveyQuestion.ResponseType.SINGLE_CHOICE,
                    "options": ["Founder", "Manager", "Individual contributor"],
                    "required": True,
                },
                {
                    "text": "Which tools do you use weekly?",
                    "response_type": SurveyQuestion.ResponseType.MULTIPLE_CHOICE,
                    "options": ["Notebooks", "Dashboards", "Custom scripts"],
                    "required": False,
                },
                {
                    "text": "Share one thing you'd improve today.",
                    "response_type": SurveyQuestion.ResponseType.FREE_TEXT,
                    "options": [],
                    "required": False,
                },
            ],
        },
        {
            "title": "Experience matrix",
            "description": "Rate each delivery channel across key moments.",
            "questions": [
                {
                    "text": "How does each channel perform?",
                    "response_type": SurveyQuestion.ResponseType.MATRIX,
                    "options": ["Excellent", "Good", "Fair", "Poor"],
                    "matrix_rows": [
                        "Account setup",
                        "Finding answers",
                        "Getting support",
                    ],
                    "matrix_columns": ["Web", "Mobile", "Chat"],
                    "required": True,
                }
            ],
        },
    ]

    return render(
        request,
        "surveys/builder.html",
        {
            "response_types": response_types,
            "sample_sections": sample_sections,
        },
    )

from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from .models import SurveyQuestion


def survey_builder(request):
    response_types = []
    feature_map = {
        SurveyQuestion.ResponseType.BINARY: {
            "supports_options": True,
            "description": _("خيار سريع بنعم/لا مع خيارات محددة مسبقاً."),
        },
        SurveyQuestion.ResponseType.SINGLE_CHOICE: {
            "supports_options": True,
            "description": _("اختر خياراً واحداً من القائمة."),
        },
        SurveyQuestion.ResponseType.MULTIPLE_CHOICE: {
            "supports_options": True,
            "description": _("اختر عدة خيارات من القائمة."),
        },
        SurveyQuestion.ResponseType.FREE_TEXT: {
            "supports_options": False,
            "description": _("دع المجيبين يكتبون إجاباتهم بحرية."),
        },
        SurveyQuestion.ResponseType.NUMERIC: {
            "supports_options": False,
            "description": _("تسجيل أعداد أو قيم رقمية متصلة."),
        },
        SurveyQuestion.ResponseType.DATE: {
            "supports_options": False,
            "description": _("اطلب تاريخاً محدداً."),
        },
        SurveyQuestion.ResponseType.DATETIME: {
            "supports_options": False,
            "description": _("تاريخ ووقت معاً."),
        },
        SurveyQuestion.ResponseType.SCALE: {
            "supports_options": False,
            "description": _("تقييمات مثل مقياس الموافقة من 1 إلى 5."),
        },
        SurveyQuestion.ResponseType.MATRIX: {
            "supports_options": True,
            "supports_matrix": True,
            "description": _("شبكة من الصفوف والأعمدة يتم تقييمها بخيارات مشتركة."),
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
            "title": _("الملف الشخصي"),
            "description": _("سمات أساسية لتقسيم المجيبين."),
            "questions": [
                {
                    "text": _("ما الوصف الأفضل لدورك؟"),
                    "response_type": SurveyQuestion.ResponseType.SINGLE_CHOICE,
                    "options": [_("مؤسس"), _("مدير"), _("عضو مساهم")],
                    "required": True,
                },
                {
                    "text": _("ما الأدوات التي تستخدمها أسبوعياً؟"),
                    "response_type": SurveyQuestion.ResponseType.MULTIPLE_CHOICE,
                    "options": [_("دفاتر ملاحظات"), _("لوحات معلومات"), _("برمجيات مخصصة")],
                    "required": False,
                },
                {
                    "text": _("ما الشيء الذي تود تحسينه اليوم؟"),
                    "response_type": SurveyQuestion.ResponseType.FREE_TEXT,
                    "options": [],
                    "required": False,
                },
            ],
        },
        {
            "title": _("مصفوفة التجربة"),
            "description": _("قيّم كل قناة تقديم عبر اللحظات الأساسية."),
            "questions": [
                {
                    "text": _("كيف يعمل كل مسار؟"),
                    "response_type": SurveyQuestion.ResponseType.MATRIX,
                    "options": [_("ممتاز"), _("جيد"), _("مقبول"), _("ضعيف")],
                    "matrix_rows": [
                        _("إعداد الحساب"),
                        _("العثور على إجابات"),
                        _("الحصول على الدعم"),
                    ],
                    "matrix_columns": [_("ويب"), _("جوال"), _("دردشة")],
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

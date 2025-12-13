# Copilot instructions for QuestionsBank

- Keep user-facing copy translatable: use `gettext_lazy` in Python, `{% trans %}` in templates, and follow the existing Arabic/English `*_ar`/`*_en` field pattern with display helpers driven by `get_language`.
- Base templates extend `base.html`; load CSS/JS through `{% static %}` and the `extra_css`/`extra_js` blocks—no inline CSS/JS in templates.
- Favor vanilla Django patterns already used here: function-based views with `render`/`JsonResponse`, and timezone-aware timestamps via `django.utils.timezone` (`timezone.now()`, `make_aware`), not naive `datetime.now()`.
- Frontend behavior is plain JavaScript (no frameworks) with `fetch` + explicit `X-CSRFToken` and DOM updates; mirror the patterns in `static/js/base.js` and `static/assessment_runs/js/assessment.js`. Only add frameworks when necessary.
- Assessment progress is tracked in the session as a list of dicts (`question_id`, `rule_id`, optional `answer`) and responses keyed by stringified IDs; keep that shape when extending flows so routing/classification engines keep working.
- Models use `verbose_name`/`help_text` with gettext and set `ordering` for predictable admin/UI lists; do the same for new models/fields.
- Tests live in Django `TestCase` classes that use `Client` + `reverse` and JSON payloads; follow that style for new coverage.

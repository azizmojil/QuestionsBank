## QuestionsBank

QuestionsBank is a Django application for authoring survey waves, building assessment flows that review those surveys, and attaching indicator metadata and reusable response banks. It ships with Arabic/English copy and a plain JavaScript frontend.

### Quickstart

1. **Prerequisites:** Python 3.10+, pip, and virtualenv.
2. **Install dependencies:**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Database & migrations:** Uses SQLite by default (`db.sqlite3`). Apply migrations:
   ```bash
   python manage.py migrate
   ```
4. **Run the app:**
   ```bash
   python manage.py runserver
   ```
5. **Tests:** After installing dependencies, run:
   ```bash
   python manage.py test
   ```

### Data model (ERD)

```mermaid
erDiagram
    SURVEY ||--o{ SURVEY_VERSION : has
    SURVEY_VERSION ||--o{ SURVEY_QUESTION : includes
    SURVEY_VERSION ||--o{ ASSESSMENT_RUN : assessed_by
    ASSESSMENT_RUN ||--o{ ASSESSMENT_RESULT : captures
    ASSESSMENT_RESULT }o--|| SURVEY_QUESTION : for
    ASSESSMENT_RESULT ||--o{ ASSESSMENT_FILE : uploads
    ASSESSMENT_FILE }o--o| ASSESSMENT_OPTION : triggered_by
    ASSESSMENT_QUESTION ||--o{ ASSESSMENT_OPTION : offers
    ASSESSMENT_QUESTION ||--o{ ASSESSMENT_FLOW_RULE : routes
    ASSESSMENT_QUESTION }o--|| ASSESSMENT_QUESTION : depends_on
    ASSESSMENT_QUESTION }o--|| INDICATOR : pulls_list
    INDICATOR ||--o{ INDICATOR_LIST_ITEM : defines
    INDICATOR_LIST_ITEM ||--o{ INDICATOR_TRACKING : status
    INDICATOR ||--o{ INDICATOR_CLASSIFICATION : tagged_with
    CLASSIFICATION ||--o{ INDICATOR_CLASSIFICATION : covers
    INDICATOR_LIST_ITEM ||--o{ CLASSIFICATION_INDICATOR_LIST_ITEM : classification_items
    SURVEY_QUESTION ||--o{ QUESTION_CLASSIFICATION_RULE : classifies
    SURVEY_VERSION ||--o{ REEVALUATION_QUESTION : reevaluates
    RESPONSE_GROUP ||--o{ QNR_SURVEY_QUESTION : links
    RESPONSE_GROUP ||--o{ RESPONSE : options
```

*Notes:*
- `SURVEY_QUESTION` refers to `surveys.SurveyQuestion` (per survey version). Progress is stored against these questions even though navigation is handled by `AssessmentQuestion` nodes, keeping outcomes aligned with the canonical survey content being reviewed.
- `QNR_SURVEY_QUESTION`, `RESPONSE_GROUP`, and `RESPONSE` map to the `QnR` app models (`QnR.SurveyQuestion`, `QnR.ResponseGroup`, `QnR.Response`) used for reusable option banks.
- Uploaded `AssessmentFile` records always point back to the owning `AssessmentResult` and, when available, the triggering `AssessmentOption`. Each file references at most one option, while an option can have many uploaded files.
- Flow rules hang off a source `AssessmentQuestion` and store option-specific logic inside their `condition` text. Dynamic option types may derive choices from other assessment questions or survey questions at runtime rather than via direct foreign keys.

### Critical data points

- **Surveys:** `Survey` holds names/codes and ownership; `SurveyVersion` enforces unique labels per survey and autogenerates labels from survey code + version date; `SurveyQuestion` stores bilingual text plus optional codes/section labels.
- **Assessment flows:** `AssessmentQuestion` + `AssessmentOption` define branching nodes; `AssessmentFlowRule` stores declarative routing; `AssessmentRun`/`AssessmentResult` record progress and status per survey question; `AssessmentFile` captures uploads tied to a specific option/result; `QuestionClassificationRule` classifies completed questions; `ReevaluationQuestion` stores prompts for later waves.
- **Indicators:** `Indicator` groups `IndicatorListItem` entries; `IndicatorTracking` marks tracked/not-tracked status; `IndicatorClassification` and `ClassificationIndicatorListItem` relate indicators/items to reusable `Classification` tags.
- **Response bank:** `Response` values are grouped in `ResponseGroup` and attached to `QnR` questions, enabling reusable option sets.

Localization defaults to Arabic (`LANGUAGE_CODE="ar"`), with English available. Timestamps are timezone-aware (`Asia/Riyadh`). Static assets load from `static/` with `base.html` templates.

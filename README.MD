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

### Data model (detailed ERD with columns)

```mermaid
erDiagram
    AUTH_USER {
        bigint id PK
        varchar username
        varchar email
        varchar password
        datetime date_joined
        datetime last_login
    }

    SURVEY {
        bigint id PK
        varchar name_ar
        varchar name_en
        varchar code
        text description
        varchar status
        bigint owner_id
        datetime created_at
        datetime updated_at
    }

    SURVEY_EDITORS {
        bigint id PK
        bigint survey_id
        bigint user_id
    }

    SURVEY_VERSION {
        bigint id PK
        bigint survey_id
        varchar version_label
        date version_date
        varchar interval
        varchar status
        datetime created_at
        datetime updated_at
    }

    SURVEY_QUESTION {
        bigint id PK
        bigint survey_version_id
        varchar code
        text text_ar
        text text_en
        text help_text
        varchar section_label
        bool is_required
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_QUESTION {
        bigint id PK
        varchar text_ar
        varchar text_en
        text explanation_ar
        text explanation_en
        varchar option_type
        bool use_searchable_dropdown
        bool allow_multiple_choices
        bigint dynamic_option_source_question_id
        bigint indicator_source_id
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_OPTION {
        bigint id PK
        bigint question_id
        text text_ar
        text text_en
        text explanation_ar
        text explanation_en
        varchar response_type
        bool requires_file_upload
        text file_upload_explanation
    }

    ASSESSMENT_FLOW_RULE {
        bigint id PK
        bigint from_question_id
        text condition
        int priority
        bool is_active
        varchar description
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_RUN {
        bigint id PK
        bigint survey_version_id
        varchar label
        varchar status
        bigint created_by_id
        bigint assigned_to_id
        datetime started_at
        datetime completed_at
        text notes
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_RESULT {
        bigint id PK
        bigint assessment_run_id
        bigint survey_question_id
        varchar status
        bigint assessed_by_id
        json assessment_path
        text summary_comment
        json flags
        datetime assessed_at
    }

    ASSESSMENT_FILE {
        bigint id PK
        bigint assessment_result_id
        bigint triggering_option_id
        file file
        varchar original_filename
        text description
        bigint uploaded_by_id
        datetime uploaded_at
    }

    QUESTION_CLASSIFICATION_RULE {
        bigint id PK
        bigint survey_question_id
        varchar classification
        text condition
        int priority
        bool is_active
        varchar description
        datetime created_at
        datetime updated_at
    }

    REEVALUATION_QUESTION {
        bigint id PK
        bigint survey_version_id
        varchar text_ar
        varchar text_en
        datetime created_at
        datetime updated_at
    }

    INDICATOR {
        bigint id PK
        varchar name_ar
        varchar name_en
        varchar code
        datetime created_at
        datetime updated_at
    }

    INDICATOR_LIST_ITEM {
        bigint id PK
        bigint indicator_id
        varchar name
        varchar code
    }

    INDICATOR_TRACKING {
        bigint id PK
        bigint indicator_list_item_id
        varchar status
    }

    CLASSIFICATION {
        bigint id PK
        varchar name_ar
        varchar name_en
    }

    INDICATOR_CLASSIFICATION {
        bigint id PK
        bigint indicator_id
        bigint classification_id
    }

    CLASSIFICATION_INDICATOR_LIST_ITEM {
        bigint id PK
        bigint classification_id
        bigint indicatorlistitem_id
    }

    RESPONSE_TYPE {
        bigint id PK
        varchar name_ar
        varchar name_en
    }

    RESPONSE {
        bigint id PK
        varchar text_ar
        varchar text_en
    }

    RESPONSE_GROUP {
        bigint id PK
        varchar name
    }

    RESPONSE_GROUP_RESPONSES {
        bigint id PK
        bigint responsegroup_id
        bigint response_id
    }

    QNR_SURVEY_QUESTION {
        bigint id PK
        text text_ar
        text text_en
    }

    QNR_SURVEY_QUESTION_RESPONSE_GROUPS {
        bigint id PK
        bigint surveyquestion_id
        bigint responsegroup_id
    }

    MATRIX_ITEM {
        bigint id PK
        varchar text_ar
        varchar text_en
    }

    MATRIX_ITEM_GROUP {
        bigint id PK
        varchar name
    }

    MATRIX_ITEM_GROUP_ITEMS {
        bigint id PK
        bigint matrixitemgroup_id
        bigint matrixitem_id
    }

    SURVEY ||--o{ SURVEY_VERSION : has_versions
    SURVEY }o--|| AUTH_USER : owned_by
    SURVEY }o--o{ AUTH_USER : edited_by
    SURVEY_VERSION ||--o{ SURVEY_QUESTION : contains_questions
    SURVEY_VERSION ||--o{ ASSESSMENT_RUN : assessed_by
    SURVEY_VERSION ||--o{ REEVALUATION_QUESTION : has_reevaluation_questions

    ASSESSMENT_RUN ||--o{ ASSESSMENT_RESULT : produces_results
    ASSESSMENT_RUN }o--|| AUTH_USER : created_by
    ASSESSMENT_RUN }o--o| AUTH_USER : assigned_to

    ASSESSMENT_RESULT }o--|| SURVEY_QUESTION : assesses
    ASSESSMENT_RESULT }o--|| ASSESSMENT_RUN : belongs_to
    ASSESSMENT_RESULT }o--o| AUTH_USER : assessed_by
    ASSESSMENT_RESULT ||--o{ ASSESSMENT_FILE : has_uploaded_files

    ASSESSMENT_FILE }o--o| ASSESSMENT_OPTION : triggered_by
    ASSESSMENT_FILE }o--o| AUTH_USER : uploaded_by

    ASSESSMENT_QUESTION ||--o{ ASSESSMENT_OPTION : has_options
    ASSESSMENT_QUESTION ||--o{ ASSESSMENT_FLOW_RULE : has_routing_rules
    ASSESSMENT_QUESTION }o--o| ASSESSMENT_QUESTION : dynamic_source
    ASSESSMENT_QUESTION }o--o| INDICATOR : pulls_indicator_list

    INDICATOR ||--o{ INDICATOR_LIST_ITEM : contains_items
    INDICATOR_LIST_ITEM ||--o{ INDICATOR_TRACKING : tracking
    INDICATOR ||--o{ INDICATOR_CLASSIFICATION : tagged_with
    CLASSIFICATION ||--o{ INDICATOR_CLASSIFICATION : classifies_indicators
    INDICATOR_LIST_ITEM ||--o{ CLASSIFICATION_INDICATOR_LIST_ITEM : classified_by
    CLASSIFICATION ||--o{ CLASSIFICATION_INDICATOR_LIST_ITEM : classifies_items

    SURVEY_QUESTION ||--o{ QUESTION_CLASSIFICATION_RULE : has_classification_rules

    RESPONSE_GROUP ||--o{ RESPONSE_GROUP_RESPONSES : contains_responses
    RESPONSE }o--o{ RESPONSE_GROUP_RESPONSES : in_groups

    QNR_SURVEY_QUESTION ||--o{ QNR_SURVEY_QUESTION_RESPONSE_GROUPS : uses_groups
    RESPONSE_GROUP ||--o{ QNR_SURVEY_QUESTION_RESPONSE_GROUPS : attached

    MATRIX_ITEM_GROUP ||--o{ MATRIX_ITEM_GROUP_ITEMS : contains_items
    MATRIX_ITEM }o--o{ MATRIX_ITEM_GROUP_ITEMS : grouped
```

*Notes:*
- **Field types & constraints:** The ERD now includes precise field types (e.g., `varchar(255)`, `text`, `bool`, `json`, `file`, `date`, `datetime`) with unique constraints (UK) and foreign keys (FK) explicitly marked.
- **Many-to-Many relationships:** M2M relationships are shown via intermediate junction tables (`SURVEY_EDITORS`, `RESPONSE_GROUP_RESPONSES`, `QNR_SURVEY_QUESTION_RESPONSE_GROUPS`, `MATRIX_ITEM_GROUP_ITEMS`) to clarify the actual database structure.
- **SURVEY_QUESTION** refers to `surveys.SurveyQuestion` (per survey version). Progress is stored against these questions even though navigation is handled by `AssessmentQuestion` nodes, keeping outcomes aligned with the canonical survey content being reviewed.
- **QNR_SURVEY_QUESTION**, `RESPONSE_GROUP`, and `RESPONSE` map to the `Qbank` app models (`Qbank.SurveyQuestion`, `Rbank.ResponseGroup`, `Rbank.Response`) used for reusable option banks. `MATRIX_ITEM` and `MATRIX_ITEM_GROUP` from `Qbank` support matrix-style question construction.
- **Uploaded files:** `AssessmentFile` records always point back to the owning `AssessmentResult` and, when available, the triggering `AssessmentOption`. Each file references at most one option, while an option can have many uploaded files.
- **Flow rules:** Hang off a source `AssessmentQuestion` and store option-specific logic inside their `condition` text. Dynamic option types may derive choices from other assessment questions or survey questions at runtime rather than via direct foreign keys.
- **User relationships:** `AUTH_USER` is referenced by `SURVEY` (owner), `SURVEY_EDITORS` (M2M for editors), `ASSESSMENT_RUN` (created_by, assigned_to), `ASSESSMENT_RESULT` (assessed_by), and `ASSESSMENT_FILE` (uploaded_by).
- **Auto-generated fields:** `SURVEY_VERSION.version_label` is auto-generated from survey code, interval, and version date. Unique constraints exist on `SURVEY_VERSION (survey_id, version_label)`, `INDICATOR_LIST_ITEM (indicator_id, name)`, `INDICATOR_CLASSIFICATION (indicator_id, classification_id)`, and each M2M join table pair.

### Critical data points

- **Surveys:** `Survey` holds names/codes and ownership; `SurveyVersion` enforces unique labels per survey and autogenerates labels from survey code + version date; `SurveyQuestion` stores bilingual text plus optional codes/section labels.
- **Assessment flows:** `AssessmentQuestion` + `AssessmentOption` define branching nodes; `AssessmentFlowRule` stores declarative routing; `AssessmentRun`/`AssessmentResult` record progress and status per survey question; `AssessmentFile` captures uploads tied to a specific option/result; `QuestionClassificationRule` classifies completed questions; `ReevaluationQuestion` stores prompts for later waves.
- **Indicators:** `Indicator` groups `IndicatorListItem` entries; `IndicatorTracking` marks tracked/not-tracked status; `IndicatorClassification` and `ClassificationIndicatorListItem` relate indicators/items to reusable `Classification` tags.
- **Response bank:** `Response` values are grouped in `ResponseGroup` and attached to `QnR` questions, enabling reusable option sets.

Localization defaults to Arabic (`LANGUAGE_CODE="ar"`), with English available. Timestamps are timezone-aware (`Asia/Riyadh`). Static assets load from `static/` with `base.html` templates.

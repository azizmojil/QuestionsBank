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
        varchar(255) name_ar UK
        varchar(255) name_en UK
        varchar(50) code UK
        text description
        varchar(20) status "DRAFT, ACTIVE, ARCHIVED"
        bigint owner_id FK "AUTH_USER.id, nullable"
        datetime created_at
        datetime updated_at
    }

    SURVEY_EDITORS {
        bigint id PK
        bigint survey_id FK "SURVEY.id"
        bigint user_id FK "AUTH_USER.id"
        UK(survey_id, user_id)
    }

    SURVEY_VERSION {
        bigint id PK
        bigint survey_id FK "SURVEY.id"
        varchar(50) version_label "Generated from survey code/date/interval"
        date version_date "Default: today()"
        varchar(20) interval "M, Q, B, A"
        varchar(20) status "DRAFT, ACTIVE, LOCKED, ARCHIVED"
        datetime created_at
        datetime updated_at
        UK(survey_id, version_label)
    }

    SURVEY_QUESTION {
        bigint id PK
        bigint survey_version_id FK "SURVEY_VERSION.id"
        varchar(50) code
        text text_ar
        text text_en
        text help_text
        varchar(255) section_label
        bool is_required "Default: False"
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_QUESTION {
        bigint id PK
        varchar(512) text_ar
        varchar(512) text_en
        text explanation_ar
        text explanation_en
        varchar(50) option_type "STATIC, DYNAMIC_FROM_PREVIOUS_MULTI_SELECT, DYNAMIC_SURVEY_QUESTIONS, INDICATOR_LIST"
        bool use_searchable_dropdown "Default: False"
        bool allow_multiple_choices "Default: False"
        bigint dynamic_option_source_question_id FK "ASSESSMENT_QUESTION.id, nullable"
        bigint indicator_source_id FK "INDICATOR.id, nullable"
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_OPTION {
        bigint id PK
        bigint question_id FK "ASSESSMENT_QUESTION.id"
        text text_ar
        text text_en
        text explanation_ar
        text explanation_en
        varchar(20) response_type "PREDEFINED, FREE_TEXT, NUMERICAL, URL"
        bool requires_file_upload "Default: False"
        text file_upload_explanation
    }

    ASSESSMENT_FLOW_RULE {
        bigint id PK
        bigint from_question_id FK "ASSESSMENT_QUESTION.id"
        text condition
        int priority "Default: 0"
        bool is_active "Default: True"
        varchar(255) description
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_RUN {
        bigint id PK
        bigint survey_version_id FK "SURVEY_VERSION.id"
        varchar(100) label
        varchar(20) status "DRAFT, IN_PROGRESS, COMPLETE, CANCELLED"
        bigint created_by_id FK "AUTH_USER.id, nullable"
        bigint assigned_to_id FK "AUTH_USER.id, nullable"
        datetime started_at
        datetime completed_at
        text notes
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_RESULT {
        bigint id PK
        bigint assessment_run_id FK "ASSESSMENT_RUN.id"
        bigint survey_question_id FK "SURVEY_QUESTION.id"
        varchar(20) status "NOT_VISITED, IN_PROGRESS, COMPLETE, PENDING_UPLOAD"
        bigint assessed_by_id FK "AUTH_USER.id, nullable"
        json assessment_path "Default: []"
        text summary_comment
        json flags "Default: {}"
        datetime assessed_at "Auto-updated"
        UK(assessment_run_id, survey_question_id)
    }

    ASSESSMENT_FILE {
        bigint id PK
        bigint assessment_result_id FK "ASSESSMENT_RESULT.id"
        bigint triggering_option_id FK "ASSESSMENT_OPTION.id, nullable"
        file file
        varchar(255) original_filename
        text description
        bigint uploaded_by_id FK "AUTH_USER.id, nullable"
        datetime uploaded_at
    }

    QUESTION_CLASSIFICATION_RULE {
        bigint id PK
        bigint survey_question_id FK "SURVEY_QUESTION.id"
        varchar(100) classification
        text condition
        int priority "Default: 0"
        bool is_active "Default: True"
        varchar(255) description
        datetime created_at
        datetime updated_at
    }

    REEVALUATION_QUESTION {
        bigint id PK
        bigint survey_version_id FK "SURVEY_VERSION.id"
        varchar(512) text_ar
        varchar(512) text_en
        datetime created_at
        datetime updated_at
    }

    INDICATOR {
        bigint id PK
        varchar(255) name_ar UK
        varchar(255) name_en UK
        varchar(50) code
        datetime created_at
        datetime updated_at
    }

    INDICATOR_LIST_ITEM {
        bigint id PK
        bigint indicator_id FK "INDICATOR.id"
        varchar(255) name
        varchar(50) code
        UK(indicator_id, name)
    }

    INDICATOR_TRACKING {
        bigint id PK
        bigint indicator_list_item_id FK "INDICATOR_LIST_ITEM.id"
        varchar(20) status "TRACKED, NOT_TRACKED"
    }

    CLASSIFICATION {
        bigint id PK
        varchar(100) name_ar UK
        varchar(100) name_en UK
    }

    INDICATOR_CLASSIFICATION {
        bigint id PK
        bigint indicator_id FK "INDICATOR.id"
        bigint classification_id FK "CLASSIFICATION.id"
        UK(indicator_id, classification_id)
    }

    CLASSIFICATION_INDICATOR_LIST_ITEM {
        bigint id PK
        bigint classification_id FK "CLASSIFICATION.id"
        bigint indicatorlistitem_id FK "INDICATOR_LIST_ITEM.id"
    }

    RESPONSE_TYPE {
        bigint id PK
        varchar(100) name_ar UK
        varchar(100) name_en UK
    }

    RESPONSE {
        bigint id PK
        varchar(255) text_ar
        varchar(255) text_en
    }

    RESPONSE_GROUP {
        bigint id PK
        varchar(255) name
    }

    RESPONSE_GROUP_RESPONSES {
        bigint id PK
        bigint responsegroup_id FK "RESPONSE_GROUP.id"
        bigint response_id FK "RESPONSE.id"
        UK(responsegroup_id, response_id)
    }

    QNR_SURVEY_QUESTION {
        bigint id PK
        text text_ar
        text text_en
    }

    QNR_SURVEY_QUESTION_RESPONSE_GROUPS {
        bigint id PK
        bigint surveyquestion_id FK "QNR_SURVEY_QUESTION.id"
        bigint responsegroup_id FK "RESPONSE_GROUP.id"
        UK(surveyquestion_id, responsegroup_id)
    }

    MATRIX_ITEM {
        bigint id PK
        varchar(255) text_ar
        varchar(255) text_en
    }

    MATRIX_ITEM_GROUP {
        bigint id PK
        varchar(255) name
    }

    MATRIX_ITEM_GROUP_ITEMS {
        bigint id PK
        bigint matrixitemgroup_id FK "MATRIX_ITEM_GROUP.id"
        bigint matrixitem_id FK "MATRIX_ITEM.id"
        UK(matrixitemgroup_id, matrixitem_id)
    }

    SURVEY ||--o{ SURVEY_VERSION : "has versions"
    SURVEY }o--|| AUTH_USER : "owned by"
    SURVEY }o--o{ AUTH_USER : "edited by (via SURVEY_EDITORS)"
    SURVEY_VERSION ||--o{ SURVEY_QUESTION : "contains questions"
    SURVEY_VERSION ||--o{ ASSESSMENT_RUN : "assessed by"
    SURVEY_VERSION ||--o{ REEVALUATION_QUESTION : "has reevaluation questions"
    ASSESSMENT_RUN ||--o{ ASSESSMENT_RESULT : "produces results"
    ASSESSMENT_RUN }o--|| AUTH_USER : "created by"
    ASSESSMENT_RUN }o--o| AUTH_USER : "assigned to"
    ASSESSMENT_RESULT }o--|| SURVEY_QUESTION : "assesses"
    ASSESSMENT_RESULT }o--|| ASSESSMENT_RUN : "belongs to"
    ASSESSMENT_RESULT }o--o| AUTH_USER : "assessed by"
    ASSESSMENT_RESULT ||--o{ ASSESSMENT_FILE : "has uploaded files"
    ASSESSMENT_FILE }o--o| ASSESSMENT_OPTION : "triggered by option"
    ASSESSMENT_FILE }o--o| AUTH_USER : "uploaded by"
    ASSESSMENT_QUESTION ||--o{ ASSESSMENT_OPTION : "has options"
    ASSESSMENT_QUESTION ||--o{ ASSESSMENT_FLOW_RULE : "has routing rules"
    ASSESSMENT_QUESTION }o--o| ASSESSMENT_QUESTION : "dynamic source (self-reference)"
    ASSESSMENT_QUESTION }o--o| INDICATOR : "pulls indicator list"
    INDICATOR ||--o{ INDICATOR_LIST_ITEM : "contains items"
    INDICATOR_LIST_ITEM ||--o{ INDICATOR_TRACKING : "has tracking status"
    INDICATOR ||--o{ INDICATOR_CLASSIFICATION : "tagged with"
    CLASSIFICATION ||--o{ INDICATOR_CLASSIFICATION : "classifies indicators"
    INDICATOR_LIST_ITEM ||--o{ CLASSIFICATION_INDICATOR_LIST_ITEM : "classified by"
    CLASSIFICATION ||--o{ CLASSIFICATION_INDICATOR_LIST_ITEM : "classifies items"
    SURVEY_QUESTION ||--o{ QUESTION_CLASSIFICATION_RULE : "has classification rules"
    RESPONSE_GROUP ||--o{ RESPONSE_GROUP_RESPONSES : "contains responses"
    RESPONSE }o--o{ RESPONSE_GROUP_RESPONSES : "in groups"
    QNR_SURVEY_QUESTION ||--o{ QNR_SURVEY_QUESTION_RESPONSE_GROUPS : "uses groups"
    RESPONSE_GROUP ||--o{ QNR_SURVEY_QUESTION_RESPONSE_GROUPS : "attached via M2M"
    MATRIX_ITEM_GROUP ||--o{ MATRIX_ITEM_GROUP_ITEMS : "contains items"
    MATRIX_ITEM }o--o{ MATRIX_ITEM_GROUP_ITEMS : "grouped items"
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

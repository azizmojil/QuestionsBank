## QuestionsBank

QuestionsBank is an application for authoring survey waves, building assessment flows that review those surveys, and attaching indicators and reusable response banks.

### Data model

```mermaid
erDiagram
    AUTH_USER {
        bigint id PK
        varchar username
        varchar email
    }

    SURVEY {
        bigint id PK
        varchar name_ar
        varchar name_en
        varchar code
        text description
        datetime created_at
        datetime updated_at
    }

    SURVEY_VERSION {
        bigint id PK
        bigint survey_id FK
        varchar version_label
        date version_date
        varchar interval
        varchar status
        datetime created_at
        datetime updated_at
    }

    SURVEY_QUESTION {
        bigint id PK
        bigint survey_version_id FK
        varchar code
        text text_ar
        text text_en
        text help_text
        bool is_required
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_QUESTION {
        bigint id PK
        text text_ar
        text text_en
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
        bigint to_question_id
        text condition
        int priority
        varchar description
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_RUN {
        bigint id PK
        bigint survey_version_id
        datetime created_at
        datetime updated_at
    }

    ASSESSMENT_RESULT {
        bigint id PK
        bigint assessment_run_id
        bigint survey_question_id
        json results
        bigint assessed_by_id
        datetime assessed_at
        varchar classification
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

    QUESTION_CLASSIFICATION {
        bigint id PK
        varchar name_ar
        varchar name_en
    }

    QUESTION_CLASSIFICATION_RULE {
        bigint id PK
        bigint classification_id
        text condition
        int priority
        bool is_active
        varchar description
        datetime created_at
        datetime updated_at
    }

    INDICATOR_SOURCE {
        bigint id PK
        varchar name_ar
        varchar name_en
        varchar code
        datetime created_at
        datetime updated_at
    }

    INDICATOR {
        bigint id PK
        bigint indicator_source_id
        varchar name_ar
        varchar name_en
        varchar tracking_status
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

    QBANK_QUESTION {
        bigint id PK
        text text_ar
        text text_en
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

    SURVEY ||--o{ SURVEY_VERSION : has_versions
    SURVEY_VERSION ||--o{ SURVEY_QUESTION : contains_questions
    SURVEY_VERSION ||--|| ASSESSMENT_RUN : has_run
    ASSESSMENT_RUN ||--o{ ASSESSMENT_RESULT : captures_results
    ASSESSMENT_RESULT }o--|| SURVEY_QUESTION : for_question
    ASSESSMENT_RESULT ||--o{ ASSESSMENT_FILE : has_files
    ASSESSMENT_FILE }o--o| ASSESSMENT_OPTION : triggered_by

    ASSESSMENT_QUESTION ||--o{ ASSESSMENT_OPTION : has_options
    ASSESSMENT_QUESTION ||--o{ ASSESSMENT_FLOW_RULE : has_routing_rules
    ASSESSMENT_QUESTION }o--o| ASSESSMENT_QUESTION : dynamic_source
    ASSESSMENT_QUESTION }o--|| INDICATOR_SOURCE : pulls_indicator_items
    INDICATOR_SOURCE ||--o{ INDICATOR : contains_indicators

    QUESTION_CLASSIFICATION ||--o{ QUESTION_CLASSIFICATION_RULE : has_rules

    RESPONSE_GROUP }o--o{ RESPONSE : contains_responses
    QBANK_QUESTION }o--o{ RESPONSE_GROUP : uses_groups
    MATRIX_ITEM_GROUP }o--o{ MATRIX_ITEM : contains_items
```

### Rule JSON used by routing and classification

Both engines expect a lightweight JSON payload shaped as:

```json
{
  "logic": "AND",
  "conditions": [
    {"question": 123, "operator": "==", "value": "Yes", "type": "value"}
  ],
  "fallback": false
}
```

- `logic` defaults to `"AND"`; use `"OR"` to short-circuit when any condition matches.
- Each condition needs a `question` (SurveyQuestion ID), an `operator` (`==`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `not in`, `contains`, `regex`), and a `value`. Add `"type": "count"` to compare the length of a multi-select answer.
- Set `"fallback": true` to create a default rule that applies when nothing else matched.
- A shorthand single-condition form is also accepted: `{"question": 123, "operator": "==", "value": "Yes"}` is automatically wrapped into the full structure.

### Future data structure improvements

- Introduce a master labels table (with Arabic/English columns) for shared enums like statuses, option types, and tracking values to keep translations consistent across apps.
- Link `QuestionClassificationRule` directly to `SurveyQuestion` for referential integrity and easier rule targeting while still allowing fallbacks.
- Store routing and classification rule versions with a `version`/`effective_from` column so changes can be audited alongside survey versions.

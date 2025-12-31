## QuestionsBank

QuestionsBank is an application for authoring survey waves, building assessment flows that review those surveys, and attaching indicators and reusable response banks.

### Data model

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

    SURVEY_VERSION {
        bigint id PK
        bigint survey_id
        varchar version_label
        date version_date
        varchar interval
        datetime created_at
        datetime updated_at
    }

    SURVEY_SECTION {
        bigint id PK
        bigint survey_version_id
        varchar title_ar
        varchar title_en
        text description_ar
        text description_en
        int order
        datetime created_at
        datetime updated_at
    }

    SURVEY_QUESTION {
        bigint id PK
        bigint survey_version_id
        bigint section_id
        varchar code
        text text_ar
        text text_en
        text help_text
        bigint response_group_id
        bigint response_type_id
        bigint matrix_item_group_id
        bool is_matrix
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

    QBANK_SURVEY_QUESTION {
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

    RESPONSE_GROUP }o--o{ RESPONSE : contains_responses

    QBANK_SURVEY_QUESTION }o--o{ RESPONSE_GROUP : uses_groups

    MATRIX_ITEM_GROUP }o--o{ MATRIX_ITEM : contains_items
```

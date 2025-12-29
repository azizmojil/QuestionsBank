# Assessment Classification Engine – Technical Documentation

**Module:** `assessment_runs.engine`
**Version:** 1.0
**Updated:** 2025-12-25
**Owner:** Survey/Assessment Engineering Team

---

## 1. Introduction

The Assessment Classification Engine is responsible for dynamically assigning classifications to questions based on collected responses and a set of defined classification rules.

Classification rules are stored in the backend (`ClassificationRule` in `indicators` app) as JSON objects and describe conditions under which a question receives a specific classification (e.g., "High Risk", "Compliant").

**Key design principles:**

* Rules belong to a **Classification** (e.g., "High Risk").
* Rules target a specific **SurveyQuestion**.
* Rules are evaluated against all responses collected so far.
* A question can have multiple classifications if multiple rules match (though typically one primary classification is used).
* The engine supports multilingual matching (Arabic/English) for answer values.

This document defines the classification rule format, evaluation semantics, and API usage.

## 2. Architecture Overview

```text
ClassificationRule (JSON Conditions)
            |
            V
ClassificationEngine.classify_question(question, responses)
            |
         Result
            |
            V
ClassificationResult (Classification + Rule)
```

Each rule expresses:

* When a specific classification should be applied to a question.
* Based on the answer to that question (or potentially others).
* Using declarative JSON logic.

## 3. Rule JSON Specification

A classification rule is a JSON object stored in `ClassificationRule.rule`.

### 3.1 Structure

```json
{
  "logic": "AND",
  "conditions": [
    { },
    { }
  ],
  "fallback": false
}
```

### Fields

| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `logic` | "AND" or "OR" | No (default: "AND") | Whether all conditions or any condition must match. |
| `conditions` | List of objects | Yes (unless `fallback = true`) | Declarative conditions that must evaluate to true. |
| `fallback` | Boolean | No | Executes if no other rule matches. Cannot contain conditions. |

## 4. Condition Types

Two condition types are supported:

* **VALUE conditions:** Compare an answer to a value using operators.
* **COUNT conditions:** Evaluate the number of selected options in a multi-select question.

Both types may be mixed within the same rule.

## 5. VALUE Conditions

### 5.1 Format

```json
{
  "question": 10,
  "operator": "==",
  "value": "Yes"
}
```

* `question`: ID of the question whose answer is used.
* `operator`: Comparison operator.
* `value`: Expected value.

### 5.2 Supported VALUE Operators

| Operator | Meaning |
| :--- | :--- |
| `==` | Answer equals value |
| `!=` | Answer not equal to value |
| `>` | Answer > value (numeric) |
| `<` | Answer < value (numeric) |
| `>=` | Answer ≥ value (numeric) |
| `<=` | Answer ≤ value (numeric) |
| `in` | Answer is (or contains) any item in a list |
| `not in` | Answer excludes all items in a list |
| `contains` | Multi-select answer contains a specific value, or substring in text |
| `regex` | Answer matches the provided regular expression |

### 5.3 Multilingual Matching

The engine automatically handles multilingual matching for `AssessmentOption` values. If the expected value matches the ID, Arabic text, or English text of an option, it is considered a match.

**Example:**
If `value` is "Yes", and the user selected an option with `text_ar="نعم"` and `text_en="Yes"`, the condition `== "Yes"` will evaluate to true.

## 6. COUNT Conditions

A COUNT condition evaluates the number of answers provided to a question.

### 6.1 Format

```json
{
  "type": "count",
  "question": 22,
  "operator": ">",
  "value": 1
}
```

* `type`: Must be `"count"`.
* `question`: ID of the question.
* `operator`: Numeric comparison operator.
* `value`: Integer count to compare against.

## 7. Rule Evaluation Model

**Given:**
* `question`: The `AssessmentQuestion` being classified.
* `responses`: `dict[str → answer]` – mapping of question IDs to answers.

**The engine proceeds as follows:**

1.  Load all `ClassificationRule` objects.
2.  Filter rules to find those relevant to the current `question`.
    * A rule is relevant if it contains a condition targeting the `question.id`.
3.  Evaluate relevant rules in priority order (if priority is defined) or database order.
4.  For each rule:
    * Evaluate conditions against `responses`.
    * If the rule evaluates to true, return the associated `Classification`.
5.  If no rule matches, return `None`.

## 8. Classification Engine Public API

The classification engine is implemented as a class:

```python
ClassificationEngine.classify_question(
    question: AssessmentQuestion | int,
    responses: Dict[str, Any]
) -> ClassificationResult
```

### 8.1 Parameters

* **`question`**: The `AssessmentQuestion` object or ID to classify.
* **`responses`**: A dictionary mapping `question_id -> answer`.

### 8.2 Return Value

`ClassificationResult` is a data class:

```python
@dataclass
class ClassificationResult:
    question: AssessmentQuestion
    classification: Optional[Classification]
    rule: Optional[ClassificationRule]
```

* **`question`**: The question being classified.
* **`classification`**: The assigned classification, or `None`.
* **`rule`**: The rule that triggered the classification (if any).

## 9. Example Usage

```python
from assessment_runs.engine import ClassificationEngine

# 1. Initialize engine
engine = ClassificationEngine()

# 2. Prepare responses
responses = {
    "1": "Yes",
    "2": ["Option A", "Option B"]
}

# 3. Classify a question
result = engine.classify_question(question_id=1, responses=responses)

if result.classification:
    print(f"Question 1 is classified as: {result.classification}")
```

# Assessment Flow Routing Engine – Technical Documentation

**Module:** `assessment_flow.engine`
**Version:** 1.0
**Updated:** 2025-12-10
**Owner:** Survey/Assessment Engineering Team

---

## 1. Introduction

The Assessment Flow Routing Engine is responsible for dynamically determining the next question in an assessment based on all collected responses and a set of globally defined routing rules.

Routing rules are stored in the backend (`AssessmentFlowRule`) as JSON objects and describe conditions under which a question becomes the next question to show.

**Key design principles:**

* Rules belong to the **destination** question.
* Rules do not depend on the last answered question.
* Rules are evaluated globally against all responses.
* No rule can trigger more than once in a single assessment run.
* If no rule matches, the assessment ends.

This document defines the routing rule format, evaluation semantics, and API usage.

## 2. Architecture Overview

```text
AssessmentFlowRule (JSON Conditions)
            |
            V
RoutingEngine.get_next(responses, used_rule_ids)
            |
         Result
            |
            V
Next Question (or None)
```

Each rule expresses:

* When this question should be shown next
* Based on all prior answers
* Using declarative JSON logic

There is no concept of “from question” routing in the rule JSON. The engine simply tests whether a question’s rule conditions match the current global state. Once a rule fires, its `id` is added to `used_rule_ids`, ensuring it cannot fire again.

## 3. Rule JSON Specification

A routing rule is a JSON object stored in `AssessmentFlowRule.condition`.

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

### 5.3 VALUE Condition Examples

**Example 1 – Simple equality**

```json
{
  "conditions": [
    {
      "question": 15,
      "operator": "==",
      "value": "No"
    }
  ]
}
```

**Example 2 – Answer in a set of options**

```json
{
  "conditions": [
    {
      "question": 5,
      "operator": "in",
      "value": ["A", "C"]
    }
  ]
}
```
* If the answer is "A" → match
* If the answer is ["A", "Z"] → match
* If the answer is "B" → no match

## 6. COUNT Conditions

A COUNT condition evaluates the number of answers provided to a question. This is especially useful for multi-select questions.

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

### 6.2 Count Semantics

Given the stored answer:

* `None` → count = 0
* Scalar (e.g. "A", 5) → count = 1
* List / tuple / set (e.g. `["A", "B"]`) → count = length of container

### 6.3 Supported COUNT Operators

| Operator | Meaning |
| :--- | :--- |
| `==` | Count equals value |
| `!=` | Count does not equal value |
| `>` | Count greater than value |
| `<` | Count less than value |
| `>=` | Count greater than or equal |
| `<=` | Count less than or equal |

### 6.4 COUNT Condition Examples

**Example 1 – More than one answer selected**

```json
{
  "conditions": [
    {
      "type": "count",
      "question": 10,
      "operator": ">",
      "value": 1
    }
  ]
}
```

**Example 2 – Between 2 and 4 answers (inclusive)**

```json
{
  "logic": "AND",
  "conditions": [
    {
      "type": "count",
      "question": 22,
      "operator": ">=",
      "value": 2
    },
    {
      "type": "count",
      "question": 22,
      "operator": "<=",
      "value": 4
    }
  ]
}
```

## 7. Fallback Rules

Fallback rules act as a “catch-all” when no other rule matches.

### 7.1 Format

```json
{
  "fallback": true
}
```

### 7.2 Constraints

* Must not define a `conditions` array.
* Is evaluated **only** if no normal rule matches.
* Useful to ensure a final default route, if desired.
* If no normal rules and no fallback rules match, the assessment ends.

## 8. Rule Evaluation Model

**Given:**
* `responses`: `dict[int → answer]`
* `used_rule_ids`: `list[int]` – rule IDs that have already fired this run

**The engine proceeds as follows:**

1.  Load all `AssessmentFlowRule` objects.
2.  Exclude any rule whose `id` is in `used_rule_ids`.
3.  Partition rules into:
    * **Normal rules:** Rules with conditions.
    * **Fallback rules:** Rules with `{"fallback": true}` and no conditions.
4.  Evaluate all **normal rules** in database order:
    * For each rule:
        * Evaluate each condition.
        * Combine using `logic` (AND / OR).
    * If the rule result is true, select this rule and stop.
5.  If no normal rule matches:
    * Evaluate **fallback rules** (in database order).
    * The first fallback rule is selected.
6.  If no rule is selected:
    * The engine returns `next_question = None` → assessment ends.

## 9. Condition Evaluation Details

### 9.1 VALUE Conditions

For the condition:
```json
{
  "question": 7,
  "operator": "==",
  "value": "Male"
}
```
The engine:
1.  Looks up `answer = responses.get(7)`.
2.  Applies the operator:
    * `==` → `answer == "Male"`
    * `!=` → `answer != "Male"`
    * `in` → `answer in value` (or any overlap if answer is list/tuple/set)
    * `contains` → `value in answer` (for collections) or substring for strings
    * `regex` → regular expression match on `str(answer)`

**Absent answers (`None`) are generally treated as:**
* For `==` → `False`
* For `!=` → `True`
* For numeric comparisons → `False` (cannot coerce to number)
* For containment/regex → `False`
*(Implementation is configurable if semantics need to change.)*

### 9.2 COUNT Conditions

For the condition:
```json
{
  "type": "count",
  "question": 10,
  "operator": ">=",
  "value": 2
}
```
The engine:
1.  Looks up `answer = responses.get(10)`.
2.  Computes count:
    * If answer is `None` → `count = 0`
    * If answer is a list/tuple/set → `count = len(answer)`
    * Otherwise → `count = 1`
3.  Compares `count` with `value` using the numeric operator.
    * If coercion to numeric fails (invalid value), the condition is considered `False`.

## 10. Example Rules

### 10.1 Single-condition rule (simple branching)
```json
{
  "conditions": [
    {
      "question": 15,
      "operator": "==",
      "value": "No"
    }
  ]
}
```
**Meaning:** Show this question if the answer to Q15 is exactly "No".

### 10.2 Rule using COUNT only
```json
{
  "conditions": [
    {
      "type": "count",
      "question": 10,
      "operator": ">",
      "value": 1
    }
  ]
}
```
**Meaning:** Show this question if the user selected more than one option in Q10.

### 10.3 Mixed VALUE + COUNT with AND
```json
{
  "logic": "AND",
  "conditions": [
    {
      "type": "count",
      "question": 10,
      "operator": ">",
      "value": 1
    },
    {
      "question": 10,
      "operator": "contains",
      "value": "HighRisk"
    }
  ]
}
```
**Meaning:** Show this question if the user selected more than one choice in Q10 **AND** one of those choices is "HighRisk".

### 10.4 OR Logic
```json
{
  "logic": "OR",
  "conditions": [
    {
      "question": 7,
      "operator": "==",
      "value": "Male"
    },
    {
      "type": "count",
      "question": 8,
      "operator": ">=",
      "value": 2
    }
  ]
}
```
**Meaning:** Show this question if the user is male **OR** selected at least two options in Q8.

### 10.5 Fallback Rule
```json
{
  "fallback": true
}
```
**Meaning:** If no other rule matches, show this question as a default branch.

## 11. Routing Engine Public API

The routing engine is implemented as a class:

```python
RoutingEngine.get_next(
    responses: Dict[int, Any],
    used_rule_ids: Optional[Iterable[int]] = None
) -> RoutingResult
```

### 11.1 Parameters

* **`responses`**: A dictionary mapping `question_id -> answer` (scalar or collection).
* **`used_rule_ids`**: An iterable of rule primary keys that already fired during this assessment run. Any rule whose ID appears here will be ignored to ensure no rule applies twice.

### 11.2 Return Value

`RoutingResult` is a small data class:

```python
@dataclass
class RoutingResult:
    next_question: Optional[AssessmentQuestion]
    rule: Optional[AssessmentFlowRule]
```

* **`next_question`**: The question to show next, or `None` if the assessment is finished.
* **`rule`**: The rule that fired (if any). The caller must record `rule.id` in `used_rule_ids` for subsequent calls.

## 12. Guarantee: No Rule Fires Twice

This guarantee is achieved by:

1.  Caller maintains a collection of `used_rule_ids` for the current assessment run.
2.  On each call to `get_next`, the engine receives `used_rule_ids`.
3.  Rules with IDs in `used_rule_ids` are skipped during evaluation.

**Storage options for `used_rule_ids`:**
* Django session
* Associated `AssessmentRun` database model
* Redis / cache layer
* Encrypted cookies (for stateless backends)

## 13. End-of-Assessment Behavior

If:
1.  No rule matches (normal or fallback)
2.  **Or** all applicable rules are in `used_rule_ids`

Then:
```python
next_question = None
rule = None
```
This signals that there are no further questions to display and the assessment has logically ended.

## 14. Extensibility

The current design supports future condition types with minimal change:

* `"type": "sum"` – Sum numeric answers across questions.
* `"type": "score"` – Weighted scoring logic.
* `"type": "meta"` – User metadata, platform, or time-based conditions.
* `"type": "history"` – Route based on question sequence or timing.

Each new type can plug into the `_evaluate_condition` method without modifying existing rules.

## 15. Security and Validation

To ensure safe and predictable execution:

* Only a whitelisted set of operators is supported.
* Invalid JSON structures or malformed conditions cause the rule to be ignored (and logged).
* Regular expression errors are caught and treated as non-matching.
* No dynamic Python code is executed from rule JSON.
* Infinite loops are prevented by the “no rule twice per run” rule plus path design.

**It is recommended to implement:**
A model-level validator for `AssessmentFlowRule.condition` to ensure:
* Valid JSON structure
* Allowed keys only
* Valid operators
* Correct typing for `value` in COUNT conditions

## 16. Appendix: Typical Integration Pattern

**Step 1: Store answers and used rule IDs**
Maintain `responses` and `used_rule_ids` in session or DB.

**Step 2: After each answer is saved, call the engine**

```python
from assessment_flow.engine import RoutingEngine

engine = RoutingEngine()
result = engine.get_next(responses, used_rule_ids)

if result.next_question is None:
    # Assessment complete
    ...
else:
    # Record used rule (if any)
    if result.rule is not None:
        used_rule_ids.add(result.rule.id)
    # Redirect / render next question
```

**Step 3: Repeat until `next_question` is `None`.**
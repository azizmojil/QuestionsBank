from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from surveys.models import SurveyQuestion

from .models import QuestionClassificationRule

log = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """
    Holds the result of the classification engine for a single SurveyQuestion.
    """

    question: SurveyQuestion
    classification: Optional[str]
    rule: Optional[QuestionClassificationRule] = None


class ClassificationEngine:
    """
    Engine for assigning classifications to SurveyQuestions based on
    QuestionClassificationRule JSON conditions. Reuses the same JSON logic
    supported by the assessment flow routing engine.
    """

    def __init__(self, rules: Optional[Iterable[QuestionClassificationRule]] = None):
        if rules is None:
            rules = QuestionClassificationRule.objects.select_related("survey_question")
        self._rules: List[QuestionClassificationRule] = list(rules)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify_question(
            self,
            question: SurveyQuestion | int,
            responses: Dict[int, Any],
    ) -> ClassificationResult:
        """
        Return the classification for a single SurveyQuestion.
        """
        normalized_responses = self._normalize_responses(responses)
        return self._classify_with_normalized_responses(question, normalized_responses)

    def classify_all(self, responses: Dict[int, Any]) -> Dict[int, ClassificationResult]:
        """
        Classify all questions that have at least one rule.
        Returns a mapping of question_id -> ClassificationResult.
        """
        normalized_responses = self._normalize_responses(responses)
        question_ids = {rule.survey_question_id for rule in self._rules if rule.is_active}
        return {
            qid: self._classify_with_normalized_responses(qid, normalized_responses)
            for qid in question_ids
        }

    # ------------------------------------------------------------------
    # Internal rule evaluation
    # ------------------------------------------------------------------

    def _resolve_question(self, question: SurveyQuestion | int) -> SurveyQuestion:
        if isinstance(question, SurveyQuestion):
            return question
        try:
            return SurveyQuestion.objects.get(pk=question)
        except SurveyQuestion.DoesNotExist as exc:
            raise ValueError(f"SurveyQuestion with id {question} does not exist") from exc

    def _classify_with_normalized_responses(
            self,
            question: SurveyQuestion | int,
            responses: Dict[str, Any],
    ) -> ClassificationResult:
        question_obj = self._resolve_question(question)
        matched_rule = self._find_matching_rule(question_obj.id, responses)

        if matched_rule is not None:
            return ClassificationResult(
                question=question_obj,
                classification=matched_rule.classification,
                rule=matched_rule,
            )

        return ClassificationResult(question=question_obj, classification=None, rule=None)

    @staticmethod
    def _normalize_responses(responses: Dict[int, Any]) -> Dict[str, Any]:
        return {str(k): v for k, v in responses.items()}

    def _find_matching_rule(
            self,
            question_id: int,
            responses: Dict[str, Any],
    ) -> Optional[QuestionClassificationRule]:
        """
        Iterate over all rules for the question, return the first matching rule.
        """
        available_rules = [
            r for r in self._rules
            if r.survey_question_id == question_id and r.is_active
        ]

        available_rules.sort(key=lambda r: (r.priority, r.id))

        for rule in available_rules:
            raw = getattr(rule, "condition", None)

            try:
                if isinstance(raw, str):
                    if raw.strip():
                        rule_dict = json.loads(raw)
                    else:
                        continue
                elif isinstance(raw, dict):
                    rule_dict = raw
                else:
                    continue

                if self._evaluate_rule_dict(rule_dict, responses):
                    return rule

            except json.JSONDecodeError:
                log.warning("Invalid JSON in classification rule %s", getattr(rule, "pk", "<no-pk>"))
                continue
            except Exception as exc:
                log.warning(
                    "Error evaluating classification rule %s: %s",
                    getattr(rule, "pk", "<no-pk>"),
                    exc,
                    exc_info=True,
                )
                continue

        return None

    def _evaluate_rule_dict(
            self,
            rule_dict: Any,
            responses: Dict[str, Any],
    ) -> bool:
        """
        Evaluate a rule JSON dict against responses.
        """
        if not isinstance(rule_dict, dict):
            return False

        if rule_dict.get("fallback") is True:
            return True

        conditions = rule_dict.get("conditions")
        if not conditions:
            return False

        logic = (rule_dict.get("logic") or "AND").upper()

        results: List[bool] = []
        for cond in conditions:
            if not isinstance(cond, dict):
                results.append(False)
                continue
            res = self._evaluate_condition(cond, responses)
            results.append(res)

        if not results:
            return False

        if logic == "AND":
            return all(results)
        return any(results)

    def _evaluate_condition(
            self,
            cond: Dict[str, Any],
            responses: Dict[str, Any],
    ) -> bool:
        cond_type = cond.get("type") or "value"
        question_id = cond.get("question")
        operator = cond.get("operator")
        expected = cond.get("value")

        if not question_id:
            return False

        answer = responses.get(str(question_id))

        if cond_type == "count":
            count = self._coerce_count(answer)
            return self._compare_numeric(count, operator, expected)

        return self._evaluate_value_condition(answer, operator, expected)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_count(answer: Any) -> int:
        if answer is None:
            return 0
        if isinstance(answer, (list, tuple, set)):
            return len(answer)
        return 1

    def _evaluate_value_condition(
            self,
            answer: Any,
            operator: str,
            expected: Any,
    ) -> bool:
        if operator in ("==", "!=") and answer is None:
            return operator == "!="

        if operator == "==":
            return str(answer) == str(expected)
        if operator == "!=":
            return str(answer) != str(expected)

        if operator in (">", "<", ">=", "<="):
            return self._compare_numeric(answer, operator, expected)

        if operator == "in":
            if not isinstance(expected, (list, tuple, set)):
                return False
            if isinstance(answer, (list, tuple, set)):
                return any(str(a) in [str(e) for e in expected] for a in answer)
            return str(answer) in [str(e) for e in expected]

        if operator == "not in":
            if not isinstance(expected, (list, tuple, set)):
                return False
            if isinstance(answer, (list, tuple, set)):
                return all(str(a) not in [str(e) for e in expected] for a in answer)
            return str(answer) not in [str(e) for e in expected]

        if operator == "contains":
            if isinstance(answer, (list, tuple, set)):
                return str(expected) in [str(a) for a in answer]
            if isinstance(answer, str):
                return str(expected) in answer
            return False

        if operator == "regex":
            if answer is None:
                return False
            try:
                return re.search(str(expected), str(answer)) is not None
            except re.error:
                return False
        return False

    @staticmethod
    def _compare_numeric(
            actual: Any,
            operator: str,
            expected: Any,
    ) -> bool:
        try:
            a = float(actual)
            b = float(expected)
        except (TypeError, ValueError):
            return False

        if operator == ">":
            return a > b
        if operator == "<":
            return a < b
        if operator == ">=":
            return a >= b
        if operator == "<=":
            return a <= b
        if operator == "==":
            return a == b
        if operator == "!=":
            return a != b
        return False

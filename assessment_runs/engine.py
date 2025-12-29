from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from assessment_flow.models import AssessmentOption
from surveys.models import SurveyQuestion
from .models import QuestionClassification, QuestionClassificationRule

log = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """
    Holds the result of the classification engine for a single SurveyQuestion.
    """

    question: SurveyQuestion
    classification: Optional[QuestionClassification]
    rule: Optional[QuestionClassificationRule] = None


class ClassificationEngine:
    """
    Engine for assigning classifications to SurveyQuestions based on
    QuestionClassificationRule JSON conditions.
    """

    def __init__(self, rules: Optional[Iterable[QuestionClassificationRule]] = None):
        if rules is None:
            rules = QuestionClassificationRule.objects.select_related("classification").filter(is_active=True)
        self._rules: List[QuestionClassificationRule] = list(rules)

    def classify_question(
            self,
            question: SurveyQuestion | int,
            responses: Dict[str, Any],
    ) -> ClassificationResult:
        """
        Return the classification for a single SurveyQuestion.
        """
        question_obj = self._resolve_question(question)
        
        # Find a rule that applies to this question and evaluates to True
        matched_rule = self._find_matching_rule(question_obj.id, responses)

        if matched_rule is not None:
            return ClassificationResult(
                question=question_obj,
                classification=matched_rule.classification,
                rule=matched_rule,
            )

        return ClassificationResult(question=question_obj, classification=None, rule=None)

    def _resolve_question(self, question: SurveyQuestion | int) -> SurveyQuestion:
        if isinstance(question, SurveyQuestion):
            return question
        try:
            return SurveyQuestion.objects.get(pk=question)
        except SurveyQuestion.DoesNotExist as exc:
            raise ValueError(f"SurveyQuestion with id {question} does not exist") from exc

    def _find_matching_rule(
            self,
            question_id: int,
            responses: Dict[str, Any],
    ) -> Optional[QuestionClassificationRule]:
        """
        Iterate over all rules. For each rule, check if it targets the given question_id
        AND if the condition evaluates to True.
        """
        for rule in self._rules:
            rule_dict = self._load_rule_dict(getattr(rule, "condition", None), getattr(rule, "pk", "<no-pk>"))
            if not rule_dict:
                continue

            try:
                if not self._is_rule_relevant_for_question(rule_dict, question_id):
                    continue

                if self._evaluate_rule_dict(rule_dict, responses):
                    return rule

            except Exception as exc:
                log.warning(
                    "Error evaluating classification rule %s: %s",
                    getattr(rule, "pk", "<no-pk>"),
                    exc,
                    exc_info=True,
                )
                continue

        return None

    def _load_rule_dict(self, raw: Any, rule_id: Any) -> Optional[Dict[str, Any]]:
        """
        Normalize stored JSON into a dict and allow shorthand single-condition payloads.
        """
        if raw is None:
            return None

        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return None
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                log.warning("Invalid JSON in classification rule %s", rule_id)
                return None

        if not isinstance(raw, dict):
            return None

        if raw.get("fallback") is True and not raw.get("conditions"):
            return {"fallback": True}

        if "conditions" not in raw and {"question", "operator", "value"}.issubset(raw.keys()):
            return {
                "logic": "AND",
                "conditions": [raw],
                "fallback": raw.get("fallback", False),
            }
        return raw

    def _is_rule_relevant_for_question(self, rule_dict: Dict, question_id: int) -> bool:
        """
        Check if the rule contains a condition targeting the given question_id.
        """
        if rule_dict.get("fallback") is True:
            return True

        conditions = rule_dict.get("conditions", [])
        for cond in conditions:
            if not isinstance(cond, dict):
                continue
            q_id = cond.get("question")
            if q_id and int(q_id) == question_id:
                return True
        return False

    def _evaluate_rule_dict(
            self,
            rule_dict: Any,
            responses: Dict[str, Any],
    ) -> bool:
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

        return self._evaluate_value_condition(answer, operator, expected, question_id=int(question_id))

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
            question_id: Optional[int] = None,
    ) -> bool:
        def check_translated_equality(qid: int, ans: Any, exp: Any) -> bool:
            s_ans = str(ans).strip()
            s_exp = str(exp).strip()
            options = AssessmentOption.objects.filter(question_id=qid)
            for opt in options:
                matches_exp = (
                    str(opt.id) == s_exp or
                    (opt.text_ar and opt.text_ar.strip() == s_exp) or
                    (opt.text_en and opt.text_en.strip() == s_exp)
                )
                if matches_exp:
                    matches_ans = (
                        str(opt.id) == s_ans or
                        (opt.text_ar and opt.text_ar.strip() == s_ans) or
                        (opt.text_en and opt.text_en.strip() == s_ans)
                    )
                    if matches_ans:
                        return True
            return False

        def are_values_equal(ans: Any, exp: Any, qid: Optional[int]) -> bool:
            if str(ans) == str(exp):
                return True
            if qid is not None:
                return check_translated_equality(qid, ans, exp)
            return False

        if operator in ("==", "!=") and answer is None:
            return operator == "!="

        if operator == "==":
            return are_values_equal(answer, expected, question_id)
        if operator == "!=":
            return not are_values_equal(answer, expected, question_id)

        if operator in (">", "<", ">=", "<="):
            return self._compare_numeric(answer, operator, expected)

        if operator == "in":
            if not isinstance(expected, (list, tuple, set)):
                return False
            answer_list = answer if isinstance(answer, (list, tuple, set)) else [answer]
            for ans in answer_list:
                for exp in expected:
                    if are_values_equal(ans, exp, question_id):
                        return True
            return False

        if operator == "not in":
            if not isinstance(expected, (list, tuple, set)):
                return False
            answer_list = answer if isinstance(answer, (list, tuple, set)) else [answer]
            for ans in answer_list:
                for exp in expected:
                    if are_values_equal(ans, exp, question_id):
                        return False
            return True

        if operator == "contains":
            if isinstance(answer, (list, tuple, set)):
                for ans in answer:
                    if are_values_equal(ans, expected, question_id):
                        return True
                return False
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

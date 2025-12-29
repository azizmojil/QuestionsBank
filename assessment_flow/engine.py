from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from django.db.models import QuerySet

from .models import AssessmentQuestion, AssessmentFlowRule, AssessmentOption

log = logging.getLogger(__name__)


@dataclass
class RoutingResult:
    """
    Holds the result of the routing engine.
    """
    next_question: Optional[AssessmentQuestion]
    rule: Optional[AssessmentFlowRule] = None


class RoutingEngine:
    """
    Core engine for resolving the next AssessmentQuestion based on
    stored AssessmentFlowRule JSON and user responses.
    """

    def __init__(self, rules: Optional[Iterable[AssessmentFlowRule]] = None):
        """
        :param rules: Optional pre-fetched iterable of AssessmentFlowRule.
                      If None, engine will query all rules.
        """
        if rules is None:
            # We load all rules because the engine evaluates them globally.
            # 'to_question' is the DESTINATION question.
            rules = AssessmentFlowRule.objects.select_related("to_question").all()
        self._rules: List[AssessmentFlowRule] = list(rules)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_next_question(
            self,
            responses: Dict[int, Any],
            used_rule_ids: Optional[Iterable[int]] = None,
    ) -> RoutingResult:
        """
        Determine the next AssessmentQuestion to route to.

        :param responses: Mapping of question_id -> answer.
        :param used_rule_ids: Set of rule IDs that have already fired.
        :return: The next AssessmentQuestion to show, or None if no rule matches.
        """
        matched_rule = self._find_matching_rule(responses, used_rule_ids)

        if matched_rule is not None:
            # The rule is attached to the question we want to show next.
            return RoutingResult(
                next_question=matched_rule.to_question,
                rule=matched_rule
            )

        # If no rule matched, end the assessment.
        return RoutingResult(next_question=None)

    # ------------------------------------------------------------------
    # Internal rule evaluation
    # ------------------------------------------------------------------

    def _find_matching_rule(
            self,
            responses: Dict[int, Any],
            used_rule_ids: Optional[Iterable[int]] = None,
    ) -> Optional[AssessmentFlowRule]:
        """
        Iterate over all rules, return the first matching rule.
        Skips rules that are in used_rule_ids.
        """
        used_ids = set(used_rule_ids) if used_rule_ids else set()

        # Filter out used rules first
        available_rules = [r for r in self._rules if r.id not in used_ids]

        # Sort rules: Priority (lower is better), then ID
        # (Assuming the list isn't already sorted perfectly by the DB)
        available_rules.sort(key=lambda r: (r.priority, r.id))

        for rule in available_rules:
            rule_dict = self._load_rule_dict(getattr(rule, "condition", None), getattr(rule, "pk", "<no-pk>"))
            if not rule_dict:
                continue

            try:
                if self._evaluate_rule_dict(rule_dict, responses):
                    return rule

            except Exception as exc:
                log.warning(
                    "Error evaluating routing rule %s: %s",
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
                log.warning(f"Invalid JSON in rule {rule_id}")
                return None

        if not isinstance(raw, dict):
            return None

        if raw.get("fallback") is True and not raw.get("conditions"):
            return {"fallback": True}

        if "conditions" not in raw and {"question", "operator"}.issubset(raw.keys()):
            return {
                "logic": "AND",
                "conditions": [raw],
                "fallback": raw.get("fallback", False),
            }
        return raw

    def _evaluate_rule_dict(
            self,
            rule_dict: Any,
            responses: Dict[int, Any],
    ) -> bool:
        """
        Evaluate a rule JSON dict against responses.
        """
        if not isinstance(rule_dict, dict):
            return False

        # Check for explicit fallback
        if rule_dict.get("fallback") is True:
            return True

        conditions = rule_dict.get("conditions")
        if not conditions:
            # No conditions and not a fallback -> don't match
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
        else:  # "OR"
            return any(results)

    def _evaluate_condition(
            self,
            cond: Dict[str, Any],
            responses: Dict[int, Any],
    ) -> bool:
        """
        Evaluate a single condition.
        """
        cond_type = cond.get("type") or "value"
        question_id = cond.get("question")
        operator = cond.get("operator")
        expected = cond.get("value")

        # Question ID is required for value/count checks
        if not question_id:
            return False

        # Convert question_id to string for lookup if responses uses string keys
        # The view uses str(question.id) for keys.
        answer = responses.get(str(question_id))

        # If not found, try int key just in case
        if answer is None:
            answer = responses.get(int(question_id))

        if cond_type == "count":
            count = self._coerce_count(answer)
            return self._compare_numeric(count, operator, expected)

        # default: value condition
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
        # Scalar value counts as 1
        return 1

    def _check_translated_equality(self, question_id: int, answer: Any, expected: Any) -> bool:
        """
        Check if answer and expected refer to the same AssessmentOption,
        matching by ID, Arabic text, or English text.
        """
        s_answer = str(answer).strip()
        s_expected = str(expected).strip()

        # Optimization: If both are identical strings, we already checked that.
        # But this method is called when direct equality failed.

        # Fetch options for this question
        options = AssessmentOption.objects.filter(question_id=question_id)

        for opt in options:
            # Check if this option matches 'expected'
            matches_expected = (
                str(opt.id) == s_expected or
                (opt.text_ar and opt.text_ar.strip() == s_expected) or
                (opt.text_en and opt.text_en.strip() == s_expected)
            )

            if matches_expected:
                # If this is the expected option, check if 'answer' also matches it
                matches_answer = (
                    str(opt.id) == s_answer or
                    (opt.text_ar and opt.text_ar.strip() == s_answer) or
                    (opt.text_en and opt.text_en.strip() == s_answer)
                )
                if matches_answer:
                    return True

        return False

    def _are_values_equal(self, answer: Any, expected: Any, question_id: Optional[int]) -> bool:
        # 1. Direct string comparison
        if str(answer) == str(expected):
            return True
        
        # 2. Translation/ID lookup
        if question_id is not None:
            return self._check_translated_equality(question_id, answer, expected)
            
        return False

    def _evaluate_value_condition(
            self,
            answer: Any,
            operator: str,
            expected: Any,
            question_id: Optional[int] = None,
    ) -> bool:
        if operator in ("==", "!=") and answer is None:
            return operator == "!="

        if operator == "==":
            return self._are_values_equal(answer, expected, question_id)
            
        if operator == "!=":
            return not self._are_values_equal(answer, expected, question_id)

        if operator in (">", "<", ">=", "<="):
            return self._compare_numeric(answer, operator, expected)

        if operator == "in":
            if not isinstance(expected, (list, tuple, set)):
                return False
            
            answer_list = answer if isinstance(answer, (list, tuple, set)) else [answer]
            # Check if ANY item in answer_list matches ANY item in expected
            for ans in answer_list:
                for exp in expected:
                    if self._are_values_equal(ans, exp, question_id):
                        return True
            return False

        if operator == "not in":
            if not isinstance(expected, (list, tuple, set)):
                return False
            
            answer_list = answer if isinstance(answer, (list, tuple, set)) else [answer]
            # Check if ALL items in answer_list do NOT match ANY item in expected
            for ans in answer_list:
                for exp in expected:
                    if self._are_values_equal(ans, exp, question_id):
                        return False
            return True

        if operator == "contains":
            if isinstance(answer, (list, tuple, set)):
                # Check if 'expected' is in the answer list (using fuzzy match)
                for ans in answer:
                    if self._are_values_equal(ans, expected, question_id):
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

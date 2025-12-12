from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from django.db.models import QuerySet

from .models import AssessmentQuestion, AssessmentFlowRule

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
            # 'from_question' is the DESTINATION question.
            rules = AssessmentFlowRule.objects.select_related("from_question").all()
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
                next_question=matched_rule.from_question,
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
            raw = getattr(rule, "condition", None)

            # Parse the JSON condition
            import json
            try:
                if isinstance(raw, str):
                    # If it's a string, try to parse it as JSON
                    if raw.strip():
                        rule_dict = json.loads(raw)
                    else:
                        # Empty string condition -> treat as fallback/always true?
                        # Or ignore? Let's assume empty = ignore for safety unless explicit fallback.
                        continue
                elif isinstance(raw, dict):
                    rule_dict = raw
                else:
                    continue
                
                if self._evaluate_rule_dict(rule_dict, responses):
                    return rule

            except json.JSONDecodeError:
                log.warning(f"Invalid JSON in rule {rule.id}")
                continue
            except Exception as exc:
                log.warning(
                    "Error evaluating routing rule %s: %s",
                    getattr(rule, "pk", "<no-pk>"),
                    exc,
                    exc_info=True,
                )
                continue

        return None

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
        # Scalar value counts as 1
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
            # String comparison for safety
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

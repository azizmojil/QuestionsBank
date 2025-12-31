from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from assessment_flow.engine import RoutingEngine as AssessmentRoutingEngine
from assessment_flow.engine import RoutingResult as AssessmentRoutingResult

from .models import SurveyQuestion, SurveyRoutingRule, SurveyVersion


@dataclass
class RoutingResult:
    """Routing result for survey questions."""

    next_question: Optional[SurveyQuestion]
    rule: Optional[SurveyRoutingRule] = None


class SurveyRoutingEngine(AssessmentRoutingEngine):
    """
    Survey routing engine that reuses the assessment routing logic
    against SurveyRoutingRule objects scoped to a SurveyVersion.
    """

    def __init__(
        self,
        survey_version: SurveyVersion,
        rules: Optional[Iterable[SurveyRoutingRule]] = None,
    ):
        self.survey_version = survey_version
        rules = (
            SurveyRoutingRule.objects.filter(
                to_question__survey_version=survey_version
            ).select_related("to_question")
            if rules is None
            else rules
        )
        super().__init__(rules=rules)

    def get_next_question(
        self,
        responses: Dict[int, Any],
        used_rule_ids: Optional[Iterable[int]] = None,
    ) -> RoutingResult:
        result: AssessmentRoutingResult = super().get_next_question(
            responses=responses,
            used_rule_ids=used_rule_ids,
        )
        return RoutingResult(next_question=result.next_question, rule=result.rule)

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def _check_translated_equality(
        self,
        question_id: int,
        answer: Any,
        expected: Any,
    ) -> bool:
        """
        Survey questions do not have translated option tables like assessment
        options. Fall back to a simple string equality check.
        """
        return str(answer).strip() == str(expected).strip()

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from django.db.models import QuerySet

from .models import SurveyQuestion, SurveyVersion

log = logging.getLogger(__name__)


@dataclass
class RoutingResult:
    """
    Holds the result of the routing engine.
    """
    next_question: Optional[SurveyQuestion]
    # rule: Optional[SurveyFlowRule] = None # If we had a rule model


class SurveyRoutingEngine:
    """
    Core engine for resolving the next SurveyQuestion based on
    stored routing logic and user responses.
    """

    def __init__(self, survey_version: SurveyVersion):
        """
        :param survey_version: The survey version context.
        """
        self.survey_version = survey_version
        # In a real implementation, we would load rules here.
        # For now, we assume a simple linear flow or basic logic.
        self._questions = list(survey_version.questions.all())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_next_question(
            self,
            current_question_id: Optional[int],
            responses: Dict[int, Any],
    ) -> RoutingResult:
        """
        Determine the next SurveyQuestion to route to.

        :param current_question_id: The ID of the question just answered.
        :param responses: Mapping of question_id -> answer.
        :return: The next SurveyQuestion to show, or None if end of survey.
        """
        
        # Simple linear flow implementation for now
        if not self._questions:
            return RoutingResult(next_question=None)

        if current_question_id is None:
            # Start with the first question
            return RoutingResult(next_question=self._questions[0])

        try:
            # Find current index
            current_index = next(i for i, q in enumerate(self._questions) if q.id == current_question_id)
            
            # Return next question if available
            if current_index + 1 < len(self._questions):
                return RoutingResult(next_question=self._questions[current_index + 1])
            
        except StopIteration:
            log.warning(f"Current question {current_question_id} not found in version {self.survey_version.id}")
        
        # End of survey
        return RoutingResult(next_question=None)

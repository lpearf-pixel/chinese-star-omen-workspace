"""Frozen RuleAssessment public adapter surface.

Implementation lives in ``rule_assessment_impl`` so the public import path remains
stable while internal projection logic can be reviewed independently.
"""

from .rule_assessment_impl import (
    AssessmentBuildResultV1,
    TwoStageRetriever,
    build_rule_assessment,
    build_rule_assessment_result,
    event_to_matcher_input,
    project_matcher_result,
)

__all__ = [
    "AssessmentBuildResultV1",
    "TwoStageRetriever",
    "build_rule_assessment",
    "build_rule_assessment_result",
    "event_to_matcher_input",
    "project_matcher_result",
]

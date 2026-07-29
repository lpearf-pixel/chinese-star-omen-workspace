"""Frozen RuleAssessment public adapter surface.

The runtime orchestrator validates external retrieval boundaries while the pure
projection implementation remains isolated for deterministic review.
"""

from .rule_assessment_runtime import (
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

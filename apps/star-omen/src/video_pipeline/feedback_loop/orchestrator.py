from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence

from pydantic import BaseModel

from src.video_pipeline.contracts.external_media_v1 import ExternalAuditBundleV1
from src.video_pipeline.feedback_loop.comparison import compare_external_audit
from src.video_pipeline.feedback_loop.contracts_v1 import (
    FeedbackLoopRunV1,
    FeedbackMetricV1,
    FeedbackObservationV1,
    FeedbackOutcomeV1,
    LearningUpdateProposalV1,
    LocalEvidenceProbeV1,
    ManualPublicationHandoffV1,
)
from src.video_pipeline.feedback_loop.planner import (
    build_initial_publication_handoff,
    build_video_production_request,
    plan_improvement_candidates,
)
from src.video_pipeline.package import (
    PackageManifestV1,
    build_package_manifest,
    verify_package_members,
    write_package_atomic,
)


_POLICY_VERSION = "vfl-policy/1.0.0"
_BASE_MEMBER_PATHS = frozenset(
    {
        "external-audit-bundle.json",
        "local-evidence-probes.json",
        "feedback-observations.json",
        "improvement-candidates.json",
        "video-production-request.json",
        "manual-publication-handoff.json",
        "feedback-loop-run.json",
    }
)


@dataclass(frozen=True, slots=True)
class FeedbackLoopBuild:
    run: FeedbackLoopRunV1
    manifest: PackageManifestV1
    members: Mapping[str, bytes]

    def __post_init__(self) -> None:
        object.__setattr__(self, "members", MappingProxyType(dict(self.members)))


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _model_payload(model: BaseModel) -> dict[str, object]:
    return model.model_dump(mode="json", exclude_none=False)


def _sequence_payload(models: Sequence[BaseModel]) -> list[dict[str, object]]:
    return [_model_payload(model) for model in models]


def _derive_run_id(
    *,
    audit: ExternalAuditBundleV1,
    probes: Sequence[LocalEvidenceProbeV1],
    outcome: FeedbackOutcomeV1 | None,
    policy_version: str,
) -> str:
    preimage = {
        "audit_bundle": _model_payload(audit),
        "local_probes": _sequence_payload(probes),
        "outcome": _model_payload(outcome) if outcome is not None else None,
        "policy_version": policy_version,
    }
    digest = hashlib.sha256(_canonical_json_bytes(preimage)).hexdigest()
    return f"feedback-run:vfl:{digest}"


def _build_learning_update_proposal(
    *,
    outcome: FeedbackOutcomeV1,
    observations: Sequence[FeedbackObservationV1],
) -> LearningUpdateProposalV1:
    observation_ids = sorted(
        observation.observation_id for observation in observations
    )
    preimage = {
        "observation_ids": observation_ids,
        "outcome": _model_payload(outcome),
        "policy_version": _POLICY_VERSION,
    }
    digest = hashlib.sha256(_canonical_json_bytes(preimage)).hexdigest()
    return LearningUpdateProposalV1(
        proposal_id=f"proposal:vfl:{digest}",
        outcome_id=outcome.outcome_id,
        owner_subsystem="video_editorial",
        evidence_observation_ids=observation_ids,
        expected_benefit=(
            "Use the documented human outcome to evaluate a bounded editorial "
            "improvement without changing the completed run or applying it."
        ),
        verification_steps=[
            "Evaluate this proposal in a separately approved video-editorial task."
        ],
        rollback_requirements=[
            "Reject or revert any later owning-module change that does not improve reviewed output."
        ],
        apply_allowed=False,
    )


def _build_metrics(
    *,
    audit: ExternalAuditBundleV1,
    probes: Sequence[LocalEvidenceProbeV1],
    observations: Sequence[FeedbackObservationV1],
    candidate_count: int,
) -> list[FeedbackMetricV1]:
    counts = {
        "candidate_count": candidate_count,
        "claim_count": len(audit.claims),
        "contradiction_count": sum(
            observation.operational_disposition == "contradicted"
            for observation in observations
        ),
        "observation_count": len(observations),
        "probe_count": len(probes),
        "unresolved_count": sum(
            probe.result_state in {"unresolved", "not_searched"} for probe in probes
        ),
    }
    return [
        FeedbackMetricV1(
            metric_id=f"metric:vfl:{name.replace('_', '-')}",
            metric_name=name,
            value=float(value),
            unit="count",
        )
        for name, value in sorted(counts.items())
    ]


def build_feedback_loop_run(
    *,
    audit_bundle: ExternalAuditBundleV1,
    local_probes: Sequence[LocalEvidenceProbeV1],
    outcome: FeedbackOutcomeV1 | None = None,
    policy_version: str = _POLICY_VERSION,
) -> FeedbackLoopBuild:
    """Build one deterministic, offline feedback-loop run package in memory."""
    if policy_version != _POLICY_VERSION:
        raise ValueError(f"policy_version must equal {_POLICY_VERSION}")

    audit = ExternalAuditBundleV1.model_validate(
        audit_bundle.model_dump(mode="python")
    )
    probes = tuple(
        sorted(
            (
                LocalEvidenceProbeV1.model_validate(probe.model_dump(mode="python"))
                for probe in local_probes
            ),
            key=lambda probe: (probe.claim_id, probe.probe_id),
        )
    )
    validated_outcome = (
        FeedbackOutcomeV1.model_validate(outcome.model_dump(mode="python"))
        if outcome is not None
        else None
    )

    run_id = _derive_run_id(
        audit=audit,
        probes=probes,
        outcome=validated_outcome,
        policy_version=policy_version,
    )
    observations = compare_external_audit(
        audit_bundle=audit,
        local_probes=probes,
    )
    candidates = plan_improvement_candidates(observations=observations)
    production_request = build_video_production_request(
        audit_bundle=audit,
        observations=observations,
    )
    handoff = build_initial_publication_handoff(
        production_request=production_request
    )

    proposal = None
    if validated_outcome is not None:
        if validated_outcome.handoff_id != handoff.handoff_id:
            raise ValueError("outcome handoff_id must equal the derived handoff_id")
        handoff_payload = handoff.model_dump(mode="python")
        handoff_payload["state"] = "learning_proposal_ready"
        handoff = ManualPublicationHandoffV1.model_validate(handoff_payload)
        proposal = _build_learning_update_proposal(
            outcome=validated_outcome,
            observations=observations,
        )

    run = FeedbackLoopRunV1(
        schema_version="feedback-loop-run/v1",
        run_id=run_id,
        policy_version=policy_version,
        source_id=audit.source.source_id,
        audit_id=audit.audit.audit_id,
        local_probes=list(probes),
        observations=list(observations),
        improvement_candidates=list(candidates),
        video_production_request=production_request,
        manual_publication_handoff=handoff,
        outcome=validated_outcome,
        learning_update_proposal=proposal,
        metrics=_build_metrics(
            audit=audit,
            probes=probes,
            observations=observations,
            candidate_count=len(candidates),
        ),
    )

    members = {
        "external-audit-bundle.json": _canonical_json_bytes(_model_payload(audit)),
        "local-evidence-probes.json": _canonical_json_bytes(
            _sequence_payload(probes)
        ),
        "feedback-observations.json": _canonical_json_bytes(
            _sequence_payload(observations)
        ),
        "improvement-candidates.json": _canonical_json_bytes(
            _sequence_payload(candidates)
        ),
        "video-production-request.json": _canonical_json_bytes(
            _model_payload(production_request)
        ),
        "manual-publication-handoff.json": _canonical_json_bytes(
            _model_payload(handoff)
        ),
        "feedback-loop-run.json": _canonical_json_bytes(_model_payload(run)),
    }
    if validated_outcome is not None:
        assert proposal is not None
        members["feedback-outcome.json"] = _canonical_json_bytes(
            _model_payload(validated_outcome)
        )
        members["learning-update-proposal.json"] = _canonical_json_bytes(
            _model_payload(proposal)
        )

    manifest = build_package_manifest(package_id=run_id, members=members)
    verify_package_members(manifest, members)
    return FeedbackLoopBuild(run=run, manifest=manifest, members=members)


def _parse_canonical_member(*, path: str, content: bytes) -> object:
    try:
        payload = json.loads(content.decode("utf-8"))
        canonical = _canonical_json_bytes(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(f"canonical JSON member is invalid: {path}") from exc
    if canonical != content:
        raise ValueError(f"canonical JSON member bytes do not match: {path}")
    return payload


def publish_feedback_loop_run(
    *,
    output_dir: Path,
    build: FeedbackLoopBuild,
) -> Path:
    """Validate and atomically publish one no-replace feedback-loop package."""
    run = FeedbackLoopRunV1.model_validate(build.run.model_dump(mode="python"))
    manifest = PackageManifestV1.model_validate(build.manifest.model_dump(mode="python"))
    members = dict(build.members)
    verify_package_members(manifest, members)

    if manifest.package_id != run.run_id:
        raise ValueError("feedback-loop manifest identity does not match run")
    expected_paths = set(_BASE_MEMBER_PATHS)
    if run.outcome is not None:
        expected_paths.update(
            {"feedback-outcome.json", "learning-update-proposal.json"}
        )
    if set(members) != expected_paths:
        raise ValueError("feedback-loop member set does not match run lifecycle")

    parsed = {
        path: _parse_canonical_member(path=path, content=content)
        for path, content in members.items()
    }
    audit = ExternalAuditBundleV1.model_validate(
        parsed["external-audit-bundle.json"]
    )
    rebuilt = build_feedback_loop_run(
        audit_bundle=audit,
        local_probes=run.local_probes,
        outcome=run.outcome,
        policy_version=run.policy_version,
    )
    if (
        rebuilt.run != run
        or rebuilt.manifest != manifest
        or dict(rebuilt.members) != members
    ):
        raise ValueError("canonical feedback-loop member identity does not match build")

    return write_package_atomic(
        output_dir=output_dir,
        manifest=manifest,
        members=members,
    )


__all__ = [
    "FeedbackLoopBuild",
    "build_feedback_loop_run",
    "publish_feedback_loop_run",
]

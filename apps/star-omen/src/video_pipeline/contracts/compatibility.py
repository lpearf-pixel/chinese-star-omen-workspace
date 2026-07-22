from __future__ import annotations

from typing import Any, Mapping

from pydantic import Field

from ._common import StrictContractModel


class CompatibilityIssue(StrictContractModel):
    code: str = Field(min_length=1)
    path: str = Field(min_length=1)
    message: str = Field(min_length=1)


class CompatibilityReport(StrictContractModel):
    compatible: bool
    issues: list[CompatibilityIssue]


class ContractCompatibilityError(ValueError):
    def __init__(self, report: CompatibilityReport):
        super().__init__("contract schemas are not v1 compatible")
        self.report = report


def _issue(code: str, path: str, message: str) -> CompatibilityIssue:
    return CompatibilityIssue(code=code, path=path, message=message)


def _as_object_schema(
    schema: Mapping[str, Any], side: str
) -> tuple[dict[str, Any], list[CompatibilityIssue]]:
    issues: list[CompatibilityIssue] = []
    if schema.get("type") != "object":
        issues.append(_issue("schema_invalid", side, "root schema type must be object"))
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        issues.append(
            _issue("schema_invalid", f"{side}.properties", "properties must be an object")
        )
        properties = {}
    required = schema.get("required", [])
    if not isinstance(required, list) or not all(
        isinstance(item, str) for item in required
    ):
        issues.append(
            _issue(
                "schema_invalid",
                f"{side}.required",
                "required must be a string list",
            )
        )
        required = []
    return {"properties": properties, "required": required}, issues


def validate_contract_compatibility(
    old_schema: Mapping[str, Any],
    new_schema: Mapping[str, Any],
) -> CompatibilityReport:
    old, issues = _as_object_schema(old_schema, "old")
    new, new_issues = _as_object_schema(new_schema, "new")
    issues.extend(new_issues)

    if old_schema.get("$id") != new_schema.get("$id"):
        issues.append(_issue("schema_id_changed", "$id", "schema identity changed"))
    if old_schema.get("additionalProperties", True) is False and new_schema.get(
        "additionalProperties", True
    ) is not False:
        issues.append(
            _issue(
                "additional_properties_changed",
                "additionalProperties",
                "closed v1 schema cannot be opened",
            )
        )

    old_required = set(old["required"])
    new_required = set(new["required"])
    for name in sorted(old_required - new_required):
        issues.append(
            _issue("required_removed", f"required.{name}", "required field removed")
        )
    for name in sorted(new_required - old_required):
        issues.append(
            _issue("required_added", f"required.{name}", "new required field added")
        )

    old_properties: dict[str, Any] = old["properties"]
    new_properties: dict[str, Any] = new["properties"]
    for name in sorted(set(old_properties) - set(new_properties)):
        issues.append(
            _issue("property_removed", f"properties.{name}", "existing field removed")
        )

    stable_keywords = (
        "type",
        "enum",
        "const",
        "format",
        "pattern",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "$ref",
        "items",
        "anyOf",
        "oneOf",
        "allOf",
    )
    for name in sorted(set(old_properties) & set(new_properties)):
        old_field = old_properties[name]
        new_field = new_properties[name]
        if not isinstance(old_field, dict) or not isinstance(new_field, dict):
            issues.append(
                _issue(
                    "schema_invalid",
                    f"properties.{name}",
                    "field schema must be an object",
                )
            )
            continue
        for keyword in stable_keywords:
            if old_field.get(keyword) != new_field.get(keyword):
                code = "enum_changed" if keyword == "enum" else "field_semantics_changed"
                issues.append(
                    _issue(
                        code,
                        f"properties.{name}.{keyword}",
                        f"existing field keyword {keyword} changed",
                    )
                )

    report = CompatibilityReport(compatible=not issues, issues=issues)
    if issues:
        raise ContractCompatibilityError(report)
    return report

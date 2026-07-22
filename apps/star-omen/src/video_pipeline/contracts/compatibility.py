from __future__ import annotations

from typing import Any, Mapping, Sequence

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


def _child(path: str, name: str) -> str:
    return f"{path}.{name}" if path else name


def _string_set(
    value: Any,
    path: str,
    issues: list[CompatibilityIssue],
) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        issues.append(_issue("schema_invalid", path, "value must be a string list"))
        return set()
    return set(value)


def _compare_sequence(
    old: Any,
    new: Any,
    path: str,
    issues: list[CompatibilityIssue],
) -> None:
    if not isinstance(old, Sequence) or isinstance(old, (str, bytes)):
        issues.append(_issue("schema_invalid", path, "old value must be an array"))
        return
    if not isinstance(new, Sequence) or isinstance(new, (str, bytes)):
        issues.append(_issue("field_semantics_changed", path, "array schema changed"))
        return
    if len(old) != len(new):
        issues.append(_issue("field_semantics_changed", path, "array length changed"))
        return
    for index, (old_item, new_item) in enumerate(zip(old, new, strict=True)):
        _compare_schema_node(old_item, new_item, f"{path}[{index}]", issues)


def _compare_object_schema(
    old: Mapping[str, Any],
    new: Mapping[str, Any],
    path: str,
    issues: list[CompatibilityIssue],
) -> None:
    old_required = _string_set(old.get("required", []), _child(path, "required"), issues)
    new_required = _string_set(new.get("required", []), _child(path, "required"), issues)
    for name in sorted(old_required - new_required):
        issues.append(
            _issue(
                "required_removed",
                _child(_child(path, "required"), name),
                "required field removed",
            )
        )
    for name in sorted(new_required - old_required):
        issues.append(
            _issue(
                "required_added",
                _child(_child(path, "required"), name),
                "new required field added",
            )
        )

    old_properties = old.get("properties", {})
    new_properties = new.get("properties", {})
    if not isinstance(old_properties, Mapping):
        issues.append(
            _issue(
                "schema_invalid",
                _child(path, "properties"),
                "old properties must be an object",
            )
        )
        old_properties = {}
    if not isinstance(new_properties, Mapping):
        issues.append(
            _issue(
                "field_semantics_changed",
                _child(path, "properties"),
                "new properties must be an object",
            )
        )
        new_properties = {}

    for name in sorted(set(old_properties) - set(new_properties)):
        issues.append(
            _issue(
                "property_removed",
                _child(_child(path, "properties"), name),
                "existing field removed",
            )
        )
    for name in sorted(set(old_properties) & set(new_properties)):
        _compare_schema_node(
            old_properties[name],
            new_properties[name],
            _child(_child(path, "properties"), name),
            issues,
        )


def _compare_definitions(
    old: Mapping[str, Any],
    new: Mapping[str, Any],
    path: str,
    issues: list[CompatibilityIssue],
) -> None:
    old_defs = old.get("$defs", {})
    new_defs = new.get("$defs", {})
    if not isinstance(old_defs, Mapping):
        issues.append(_issue("schema_invalid", _child(path, "$defs"), "$defs must be an object"))
        return
    if not isinstance(new_defs, Mapping):
        issues.append(
            _issue(
                "field_semantics_changed",
                _child(path, "$defs"),
                "$defs must remain an object",
            )
        )
        return
    for name in sorted(set(old_defs) - set(new_defs)):
        issues.append(
            _issue(
                "definition_removed",
                _child(_child(path, "$defs"), name),
                "existing definition removed",
            )
        )
    for name in sorted(set(old_defs) & set(new_defs)):
        _compare_schema_node(
            old_defs[name],
            new_defs[name],
            _child(_child(path, "$defs"), name),
            issues,
        )


def _compare_schema_node(
    old: Any,
    new: Any,
    path: str,
    issues: list[CompatibilityIssue],
) -> None:
    if not isinstance(old, Mapping):
        if old != new:
            issues.append(_issue("field_semantics_changed", path, "schema value changed"))
        return
    if not isinstance(new, Mapping):
        issues.append(_issue("field_semantics_changed", path, "schema object changed"))
        return

    old_type = old.get("type")
    new_type = new.get("type")
    if old_type != new_type:
        issues.append(
            _issue("field_semantics_changed", _child(path, "type"), "field type changed")
        )

    if "enum" in old or "enum" in new:
        if old.get("enum") != new.get("enum"):
            issues.append(_issue("enum_changed", _child(path, "enum"), "enum meaning changed"))
    if "const" in old or "const" in new:
        if old.get("const") != new.get("const"):
            issues.append(
                _issue("field_semantics_changed", _child(path, "const"), "const changed")
            )

    old_additional = old.get("additionalProperties", True)
    new_additional = new.get("additionalProperties", True)
    if isinstance(old_additional, Mapping):
        _compare_schema_node(
            old_additional,
            new_additional,
            _child(path, "additionalProperties"),
            issues,
        )
    elif old_additional != new_additional:
        issues.append(
            _issue(
                "additional_properties_changed",
                _child(path, "additionalProperties"),
                "additionalProperties policy changed",
            )
        )

    if old_type == "object" or "properties" in old or "required" in old:
        _compare_object_schema(old, new, path, issues)
    if "$defs" in old or "$defs" in new:
        _compare_definitions(old, new, path, issues)

    for keyword in ("items", "contains", "propertyNames"):
        if keyword in old or keyword in new:
            if keyword not in old or keyword not in new:
                issues.append(
                    _issue(
                        "field_semantics_changed",
                        _child(path, keyword),
                        f"{keyword} constraint changed",
                    )
                )
            else:
                _compare_schema_node(old[keyword], new[keyword], _child(path, keyword), issues)

    for keyword in ("allOf", "anyOf", "oneOf", "prefixItems"):
        if keyword in old or keyword in new:
            if keyword not in old or keyword not in new:
                issues.append(
                    _issue(
                        "field_semantics_changed",
                        _child(path, keyword),
                        f"{keyword} constraint changed",
                    )
                )
            else:
                _compare_sequence(old[keyword], new[keyword], _child(path, keyword), issues)

    handled = {
        "$defs",
        "$id",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "contains",
        "enum",
        "items",
        "oneOf",
        "prefixItems",
        "properties",
        "propertyNames",
        "required",
        "type",
    }
    annotations = {"title", "description", "examples", "$comment"}
    for keyword in sorted((set(old) | set(new)) - handled - annotations):
        if old.get(keyword) != new.get(keyword):
            issues.append(
                _issue(
                    "field_semantics_changed",
                    _child(path, keyword),
                    f"existing field keyword {keyword} changed",
                )
            )


def validate_contract_compatibility(
    old_schema: Mapping[str, Any],
    new_schema: Mapping[str, Any],
) -> CompatibilityReport:
    issues: list[CompatibilityIssue] = []
    if old_schema.get("type") != "object":
        issues.append(_issue("schema_invalid", "old", "root schema type must be object"))
    if new_schema.get("type") != "object":
        issues.append(_issue("schema_invalid", "new", "root schema type must be object"))
    if old_schema.get("$id") != new_schema.get("$id"):
        issues.append(_issue("schema_id_changed", "$id", "schema identity changed"))

    _compare_schema_node(old_schema, new_schema, "", issues)

    report = CompatibilityReport(compatible=not issues, issues=issues)
    if issues:
        raise ContractCompatibilityError(report)
    return report

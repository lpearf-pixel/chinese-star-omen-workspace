from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Annotated, Any, Mapping

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,159}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must include an explicit UTC offset")
    if value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be expressed in UTC")
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_validate_utc)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
StableId = Annotated[str, Field(min_length=1, max_length=160, pattern=_ID_RE.pattern)]
Sha256Hex = Annotated[str, Field(pattern=_SHA256_RE.pattern)]


class StrictContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


def ensure_unique(values: list[str], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must contain unique identifiers")


def canonical_contract_bytes(model: BaseModel | Mapping[str, Any]) -> bytes:
    payload: Any
    if isinstance(model, BaseModel):
        payload = model.model_dump(mode="json", exclude_none=False)
    else:
        payload = dict(model)
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

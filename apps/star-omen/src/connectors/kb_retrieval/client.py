from __future__ import annotations

import copy
from types import MethodType
from typing import Any

from .core import RetrievalCoreMixin
from .transport import KBSearchError, TransportMixin
from .two_stage import TwoStageMixin


class KBSearchRetriever(TwoStageMixin, RetrievalCoreMixin, TransportMixin):
    """Unified downstream client for official retrieval plus local primary fallback."""

    @staticmethod
    def _canonicalize_filters(
        filters: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Write only canonical filter names and reject conflicting aliases."""

        if not filters:
            return None
        canonical = dict(filters)
        legacy = canonical.get("book_id")
        current = canonical.get("kb_book_id")
        if legacy is not None and current is not None and str(legacy) != str(current):
            raise ValueError("conflicting book identifiers: book_id and kb_book_id")
        if current is None and legacy is not None:
            canonical["kb_book_id"] = legacy
        canonical.pop("book_id", None)
        return canonical

    def retrieve(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Run v2 retrieval while preserving legacy *in-process* diagnostics.

        Older downstream tests and smoke tooling intercepted ``_request`` before
        the transport canonicalized the wire body. For implicit/legacy calls we
        provide those diagnostic aliases on a shallow proxy only. Explicit v2
        calls (stage or card pool supplied) remain canonical, and the transport
        still removes aliases before a real HTTP request.
        """

        limit = kwargs.pop("limit", None)
        if kwargs.get("top_k") is None and limit is not None:
            kwargs["top_k"] = limit

        explicit_v2 = (
            kwargs.get("retrieval_stage") is not None
            or kwargs.get("card_types") is not None
        )
        if explicit_v2:
            result = super().retrieve(query, **kwargs)
        else:
            original_request = self._request
            original_filters = kwargs.get("filters")
            mode = kwargs.get("query_mode") or self._query_mode(query)
            retrieval_pool = self.RETRIEVAL_POOL_SPEC.get(
                mode,
                self.RETRIEVAL_POOL_SPEC["knowledge"],
            )
            proxy = copy.copy(self)

            def compatibility_request(
                _proxy: KBSearchRetriever,
                method: str,
                path: str,
                **request_kwargs: Any,
            ) -> dict[str, Any]:
                payload = dict(request_kwargs.get("json_payload") or {})
                payload["retrieval_pool"] = retrieval_pool
                filters = payload.get("filters")
                if isinstance(filters, dict):
                    filters = dict(filters)
                    if (
                        isinstance(original_filters, dict)
                        and original_filters.get("book_id") is not None
                    ):
                        filters["book_id"] = original_filters["book_id"]
                    payload["filters"] = filters
                request_kwargs["json_payload"] = payload
                return original_request(method, path, **request_kwargs)

            proxy._request = MethodType(compatibility_request, proxy)
            result = RetrievalCoreMixin.retrieve(proxy, query, **kwargs)

        result["payload_contract_version"] = "v2"
        result["wire_schema_version"] = result.get(
            "schema_version",
            "kb-retrieve/v2",
        )
        return result

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Search with a transitional ``limit`` alias for ``top_k``."""

        effective_top_k = top_k if top_k is not None else limit
        return RetrievalCoreMixin.search(
            self,
            query,
            top_k=effective_top_k,
            **kwargs,
        )

    def two_stage_retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Two-stage retrieval with the same ``top_k``/``limit`` contract."""

        effective_top_k = top_k if top_k is not None else limit
        return TwoStageMixin.two_stage_retrieve(
            self,
            query,
            top_k=effective_top_k,
            **kwargs,
        )


__all__ = ["KBSearchError", "KBSearchRetriever"]

"""HTTP/API error mapping and service construction."""

from __future__ import annotations

import logging
from typing import Any

from googlekit.core.configuration import ClientConfig
from googlekit.core.constants import USER_AGENT
from googlekit.core.exceptions import (
    APIError,
    ConflictError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    TransportError,
)
from googlekit.core.optional import require_extra
from googlekit.core.protocols import CredentialProvider
from googlekit.core.retries import RetryPolicy, call_with_retries

logger = logging.getLogger(__name__)


def map_http_error(exc: BaseException) -> APIError:
    """Map googleapiclient HttpError (or similar) into a GoogleKit exception."""
    resp = getattr(exc, "resp", None)
    status = getattr(resp, "status", None)
    reason = None
    request_id = None
    if resp is not None:
        headers = getattr(resp, "headers", {}) or {}
        request_id = headers.get("x-goog-request-id") or headers.get("X-Goog-Request-Id")
    get_reason = getattr(exc, "_get_reason", None)
    if callable(get_reason):
        try:
            reason = str(get_reason())
        except Exception:  # pragma: no cover
            reason = None
    message = reason or str(exc) or "Google API request failed"
    # Never include authorization headers in messages (message comes from API body).
    if status == 404:
        return NotFoundError(message, status_code=404, reason=reason, request_id=request_id)
    if status == 409 or status == 412:
        return ConflictError(message, status_code=status, reason=reason, request_id=request_id)
    if status == 429:
        retry_after = None
        if resp is not None:
            headers = getattr(resp, "headers", {}) or {}
            raw = headers.get("Retry-After") or headers.get("retry-after")
            if raw is not None:
                try:
                    retry_after = float(raw)
                except (TypeError, ValueError):
                    retry_after = None
        return RateLimitError(
            message,
            retry_after=retry_after,
            status_code=429,
            reason=reason,
            request_id=request_id,
        )
    if status == 403 and reason and "quota" in reason.lower():
        return QuotaExceededError(message, status_code=403, reason=reason, request_id=request_id)
    return APIError(message, status_code=status, reason=reason, request_id=request_id)


class Transport:
    """Builds and caches Google API discovery clients with retries."""

    def __init__(
        self,
        provider: CredentialProvider,
        config: ClientConfig | None = None,
        *,
        extra: str,
    ) -> None:
        self._provider = provider
        self._config = config or ClientConfig()
        self._extra = extra
        self._services: dict[tuple[str, str], Any] = {}

    @property
    def config(self) -> ClientConfig:
        return self._config

    @property
    def provider(self) -> CredentialProvider:
        return self._provider

    def credentials(self) -> Any:
        return self._provider.credentials()

    def get_service(self, api: str, api_version: str) -> Any:
        """Return a cached discovery service for ``api``/``api_version``."""
        require_extra(self._extra)
        key = (api, api_version)
        if key in self._services:
            return self._services[key]

        from googleapiclient.discovery import build

        creds = self.credentials()
        # google-api-python-client v2+ ships static discovery documents.
        # Use the library default (static_discovery=True); do not disable
        # discovery caching — that is a v1-era pattern.
        service = build(
            api,
            api_version,
            credentials=creds,
        )
        # Attach a descriptive user-agent via http when available.
        http = getattr(service, "_http", None)
        if http is not None and hasattr(http, "headers"):
            ua = self._config.user_agent or USER_AGENT
            try:
                http.headers["user-agent"] = ua
            except Exception:  # pragma: no cover
                logger.debug("Unable to set user-agent on service HTTP client")
        self._services[key] = service
        return service

    def execute(self, request: Any, *, retry: RetryPolicy | None = None) -> Any:
        """Execute a Google API request object with retries and error mapping."""
        policy = retry if retry is not None else self._config.retry

        def _run() -> Any:
            try:
                return request.execute()
            except Exception as exc:
                # Map HttpError; re-raise GoogleKit errors; wrap unknown transport.
                name = type(exc).__name__
                if name == "HttpError" or hasattr(exc, "resp"):
                    mapped = map_http_error(exc)
                    raise mapped from exc
                if isinstance(exc, (APIError, TransportError)):
                    raise
                raise TransportError(f"Transport failure: {exc}") from exc

        return call_with_retries(_run, policy=policy)

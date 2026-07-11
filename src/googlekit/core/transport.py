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


class _UserAgentHttp:
    """Wrap an HTTP client so every request includes a custom User-Agent.

    ``httplib2.Http.headers`` is not reliably merged by ``AuthorizedHttp.request``,
    which builds request headers from its ``headers`` argument instead.
    """

    def __init__(self, http: Any, user_agent: str) -> None:
        self._http = http
        self._user_agent = user_agent

    def request(
        self,
        uri: str,
        method: str = "GET",
        body: Any = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        merged = dict(headers or {})
        # Prefer lowercase; httplib2 normalizes, but set both for safety.
        if not any(k.lower() == "user-agent" for k in merged):
            merged["user-agent"] = self._user_agent
        return self._http.request(uri, method=method, body=body, headers=merged, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._http, name)


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
    reason_l = (reason or "").lower()
    reason_compact = reason_l.replace(" ", "").replace("_", "")

    if status == 404:
        return NotFoundError(message, status_code=404, reason=reason, request_id=request_id)
    if status == 409 or status == 412:
        return ConflictError(message, status_code=status, reason=reason, request_id=request_id)

    is_rate_limited = status == 429 or (
        status == 403
        and (
            "ratelimitexceeded" in reason_compact
            or "userratelimitexceeded" in reason_compact
            or "rate limit" in reason_l
        )
    )
    if is_rate_limited:
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
            status_code=int(status) if isinstance(status, int) else 429,
            reason=reason,
            request_id=request_id,
        )
    if status == 403 and (
        "quota" in reason_l
        or "dailylimitexceeded" in reason_compact
        or "quotaexceeded" in reason_compact
    ):
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

        from google.auth.transport.requests import AuthorizedSession
        from googleapiclient.discovery import build
        from googleapiclient.http import build_http

        creds = self.credentials()
        http = build_http()
        # Apply configured timeout to the underlying httplib2 transport.
        timeout = self._config.timeout
        if timeout is not None:
            try:
                http.timeout = float(timeout)
            except Exception:  # pragma: no cover
                logger.debug("Unable to set HTTP timeout on discovery transport")

        ua = self._config.user_agent or USER_AGENT

        try:
            from google_auth_httplib2 import AuthorizedHttp

            authorized: Any = AuthorizedHttp(creds, http=http)
            authorized = _UserAgentHttp(authorized, ua)
        except Exception:
            # Fallback: discovery build with credentials (library default http).
            authorized = None

        if authorized is not None:
            service = build(api, api_version, http=authorized)
        else:
            service = build(api, api_version, credentials=creds)
            session = getattr(service, "_http", None)
            if isinstance(session, AuthorizedSession):
                session.headers["User-Agent"] = ua
            elif session is not None:
                service._http = _UserAgentHttp(session, ua)

        self._services[key] = service
        return service

    def execute(self, request: Any, *, retry: RetryPolicy | None = None) -> Any:
        """Execute a Google API request object with retries and error mapping."""
        policy = retry if retry is not None else self._config.retry

        def _run() -> Any:
            try:
                return request.execute()
            except Exception as exc:
                name = type(exc).__name__
                if name == "HttpError" or hasattr(exc, "resp"):
                    mapped = map_http_error(exc)
                    raise mapped from exc
                if isinstance(exc, (APIError, TransportError)):
                    raise
                raise TransportError(f"Transport failure: {exc}") from exc

        return call_with_retries(_run, policy=policy)

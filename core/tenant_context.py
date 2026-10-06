"""
Enterprise SaaS Multi-Tenancy & Correlation Context
Provides tenant isolation, request correlation IDs, and contextvars management.
"""

import uuid
import contextvars
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variables for the current request
_current_tenant_id: contextvars.ContextVar[str] = contextvars.ContextVar("current_tenant_id", default="default")
_current_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("current_correlation_id", default="")
_current_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_user_id", default=None)

def get_current_tenant_id() -> str:
    """Return the active tenant ID for the current async execution context."""
    return _current_tenant_id.get()

def set_current_tenant_id(tenant_id: str) -> None:
    """Set the active tenant ID."""
    _current_tenant_id.set(tenant_id or "default")

def get_current_correlation_id() -> str:
    """Return the unique request correlation ID."""
    return _current_correlation_id.get()

def set_current_correlation_id(correlation_id: str) -> None:
    """Set the unique correlation ID."""
    _current_correlation_id.set(correlation_id)

def get_current_user_id() -> Optional[str]:
    """Return the active user ID."""
    return _current_user_id.get()

def set_current_user_id(user_id: Optional[str]) -> None:
    """Set the active user ID."""
    _current_user_id.set(user_id)


class EnterpriseContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts Tenant ID, Correlation ID, and User context from
    incoming HTTP request headers, binds them to contextvars, and returns them
    in the response headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate Correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )
        set_current_correlation_id(correlation_id)

        # Extract Tenant ID from header (can be overridden by JWT auth dependency)
        tenant_id = request.headers.get("X-Tenant-ID", "default").strip()
        if not tenant_id:
            tenant_id = "default"
        set_current_tenant_id(tenant_id)

        # Process the request
        response: Response = await call_next(request)

        # Propagate headers back to client
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Tenant-ID"] = tenant_id

        return response

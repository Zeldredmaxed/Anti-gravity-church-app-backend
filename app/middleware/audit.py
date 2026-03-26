"""Audit trail middleware — logs all write operations."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.database import async_session
from app.models.user import AuditLog
from app.utils.security import decode_token
from jose import JWTError


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs POST, PUT, DELETE requests to the audit trail."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Only log write operations that succeeded
        if request.method in ("POST", "PUT", "DELETE") and response.status_code < 400:
            try:
                user_id = None
                auth_header = request.headers.get("authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    try:
                        payload = decode_token(token)
                        user_id = int(payload.get("sub", 0))
                    except (JWTError, Exception):
                        pass

                # Extract resource from path
                path_parts = request.url.path.strip("/").split("/")
                resource = path_parts[-1] if path_parts else "unknown"
                resource_id = None
                if len(path_parts) >= 2 and path_parts[-1].isdigit():
                    resource_id = path_parts[-1]
                    resource = path_parts[-2]

                action_map = {"POST": "CREATE", "PUT": "UPDATE", "DELETE": "DELETE"}
                action = action_map.get(request.method, request.method)

                # Get client IP
                ip = request.client.host if request.client else None

                async with async_session() as session:
                    audit = AuditLog(
                        user_id=user_id,
                        action=action,
                        resource=resource,
                        resource_id=resource_id,
                        details=f"{request.method} {request.url.path}",
                        ip_address=ip,
                    )
                    session.add(audit)
                    await session.commit()
            except Exception:
                pass  # Don't let audit failures break the app

        return response

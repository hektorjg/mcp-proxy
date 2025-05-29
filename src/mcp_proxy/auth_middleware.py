"""Authentication middleware for the MCP proxy server."""

import logging
import os
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate requests using a bearer token from environment variables."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.auth_token = os.getenv("MCP_PROXY_AUTH_TOKEN")
        self.enabled = self.auth_token is not None and len(self.auth_token.strip()) > 0
        
        # Paths that don't require authentication
        self.public_paths = {"/status"}
        
        if self.enabled:
            logger.info("Token authentication is ENABLED - all endpoints except /status require authentication")
        else:
            logger.info("Token authentication is DISABLED - set MCP_PROXY_AUTH_TOKEN environment variable to enable")
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and check authentication if enabled."""
        # Skip authentication if not enabled
        if not self.enabled:
            return await call_next(request)
            
        # Allow access to public paths
        if request.url.path in self.public_paths:
            return await call_next(request)
            
        # Check for authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("Authentication failed: Missing authorization header for %s", request.url.path)
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Missing authorization header", 
                    "message": "Include 'Authorization: Bearer <token>' header"
                }
            )
            
        # Validate token format
        if not auth_header.startswith("Bearer "):
            logger.warning("Authentication failed: Invalid authorization format for %s", request.url.path)
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid authorization format", 
                    "message": "Use 'Bearer <token>' format"
                }
            )
            
        # Extract and validate token
        token = auth_header[7:]  # Remove "Bearer " prefix
        if token != self.auth_token:
            logger.warning("Authentication failed: Invalid token for %s", request.url.path)
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Invalid token", 
                    "message": "The provided token is not valid"
                }
            )
            
        # Token is valid, proceed with request
        logger.debug("Authentication successful for %s", request.url.path)
        return await call_next(request) 
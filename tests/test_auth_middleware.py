"""Tests for the authentication middleware."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_proxy.auth_middleware import TokenAuthMiddleware


@pytest.fixture
def mock_app():
    """Create a simple test app with the auth middleware."""
    async def test_endpoint(request: Request) -> Response:
        return JSONResponse({"message": "success"})

    async def status_endpoint(request: Request) -> Response:
        return JSONResponse({"status": "ok"})

    app = Starlette(
        routes=[
            Route("/test", endpoint=test_endpoint),
            Route("/status", endpoint=status_endpoint),
        ],
        middleware=[Middleware(TokenAuthMiddleware)]
    )
    return app


@pytest.fixture
def client(mock_app):
    """Create a test client."""
    return TestClient(mock_app)


def test_auth_disabled_by_default(client):
    """Test that authentication is disabled when no token is set."""
    with patch.dict(os.environ, {}, clear=True):
        # Both endpoints should be accessible without auth
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}

        response = client.get("/status")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_auth_enabled_with_token():
    """Test that authentication is enabled when token is set."""
    test_token = "test_token_12345"
    
    with patch.dict(os.environ, {"MCP_PROXY_AUTH_TOKEN": test_token}):
        app = Starlette(
            routes=[
                Route("/test", endpoint=lambda r: JSONResponse({"message": "success"})),
                Route("/status", endpoint=lambda r: JSONResponse({"status": "ok"})),
            ],
            middleware=[Middleware(TokenAuthMiddleware)]
        )
        client = TestClient(app)

        # Status endpoint should still be accessible without auth
        response = client.get("/status")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Protected endpoint should require auth
        response = client.get("/test")
        assert response.status_code == 401
        assert response.json() == {
            "error": "Missing authorization header",
            "message": "Include 'Authorization: Bearer <token>' header"
        }


def test_auth_with_correct_token():
    """Test successful authentication with correct token."""
    test_token = "test_token_12345"
    
    with patch.dict(os.environ, {"MCP_PROXY_AUTH_TOKEN": test_token}):
        app = Starlette(
            routes=[
                Route("/test", endpoint=lambda r: JSONResponse({"message": "success"})),
            ],
            middleware=[Middleware(TokenAuthMiddleware)]
        )
        client = TestClient(app)

        # Request with correct token should succeed
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.get("/test", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


def test_auth_with_incorrect_token():
    """Test authentication failure with incorrect token."""
    test_token = "test_token_12345"
    
    with patch.dict(os.environ, {"MCP_PROXY_AUTH_TOKEN": test_token}):
        app = Starlette(
            routes=[
                Route("/test", endpoint=lambda r: JSONResponse({"message": "success"})),
            ],
            middleware=[Middleware(TokenAuthMiddleware)]
        )
        client = TestClient(app)

        # Request with incorrect token should fail
        headers = {"Authorization": "Bearer wrong_token"}
        response = client.get("/test", headers=headers)
        assert response.status_code == 403
        assert response.json() == {
            "error": "Invalid token",
            "message": "The provided token is not valid"
        }


def test_auth_with_invalid_format():
    """Test authentication failure with invalid header format."""
    test_token = "test_token_12345"
    
    with patch.dict(os.environ, {"MCP_PROXY_AUTH_TOKEN": test_token}):
        app = Starlette(
            routes=[
                Route("/test", endpoint=lambda r: JSONResponse({"message": "success"})),
            ],
            middleware=[Middleware(TokenAuthMiddleware)]
        )
        client = TestClient(app)

        # Request with invalid format should fail
        headers = {"Authorization": "Basic some_token"}
        response = client.get("/test", headers=headers)
        assert response.status_code == 401
        assert response.json() == {
            "error": "Invalid authorization format",
            "message": "Use 'Bearer <token>' format"
        }


def test_auth_with_empty_token():
    """Test that empty token disables authentication."""
    with patch.dict(os.environ, {"MCP_PROXY_AUTH_TOKEN": ""}):
        app = Starlette(
            routes=[
                Route("/test", endpoint=lambda r: JSONResponse({"message": "success"})),
            ],
            middleware=[Middleware(TokenAuthMiddleware)]
        )
        client = TestClient(app)

        # Empty token should disable auth
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


def test_auth_with_whitespace_only_token():
    """Test that whitespace-only token disables authentication."""
    with patch.dict(os.environ, {"MCP_PROXY_AUTH_TOKEN": "   "}):
        app = Starlette(
            routes=[
                Route("/test", endpoint=lambda r: JSONResponse({"message": "success"})),
            ],
            middleware=[Middleware(TokenAuthMiddleware)]
        )
        client = TestClient(app)

        # Whitespace-only token should disable auth
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


def test_status_endpoint_always_public():
    """Test that /status endpoint is always accessible regardless of auth settings."""
    test_token = "test_token_12345"
    
    with patch.dict(os.environ, {"MCP_PROXY_AUTH_TOKEN": test_token}):
        app = Starlette(
            routes=[
                Route("/status", endpoint=lambda r: JSONResponse({"status": "ok"})),
                Route("/test", endpoint=lambda r: JSONResponse({"message": "success"})),
            ],
            middleware=[Middleware(TokenAuthMiddleware)]
        )
        client = TestClient(app)

        # Status should be accessible without token
        response = client.get("/status")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Test endpoint should require token
        response = client.get("/test")
        assert response.status_code == 401

        # Status should still be accessible with token
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.get("/status", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"} 
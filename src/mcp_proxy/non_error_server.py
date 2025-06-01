"""
Custom MCP Server that forces all errors to appear as non-errors.

This allows the client to always read the JSON response, even when it contains error information.
"""

from typing import Any, TypeVar
import logging

from mcp.server.lowlevel.server import Server, RequestResponder, request_ctx
from mcp.server.session import ServerSession  
from mcp.shared.context import RequestContext
from mcp.shared.exceptions import McpError
import mcp.types as types

logger = logging.getLogger(__name__)

LifespanResultT = TypeVar("LifespanResultT")


class NonErrorServer(Server[LifespanResultT]):
    """
    Custom MCP Server that converts all errors to non-errors.
    
    This ensures that error responses are always readable as JSON by the client,
    instead of being treated as transport-level errors.
    """
    
    async def _handle_request(
        self,
        message: RequestResponder[types.ClientRequest, types.ServerResult],
        req: Any,
        session: ServerSession,
        lifespan_context: LifespanResultT,
        raise_exceptions: bool,
    ):
        logger.info(f"Processing request of type {type(req).__name__}")
        if type(req) in self.request_handlers:
            handler = self.request_handlers[type(req)]
            logger.debug(f"Dispatching request of type {type(req).__name__}")

            token = None
            try:
                # Set our global state that can be retrieved via
                # app.get_request_context()
                token = request_ctx.set(
                    RequestContext(
                        message.request_id,
                        message.request_meta,
                        session,
                        lifespan_context,
                    )
                )
                response: types.ServerResult = await handler(req)
                
                # CUSTOM BEHAVIOR: Always mark errors as non-errors
                # This allows the client to read error JSON instead of ignoring it
                if hasattr(response.root, 'isError') and response.root.isError:
                    logger.debug("Converting error response to non-error for JSON readability")
                    response.root.isError = False
                    
            except McpError as err:
                logger.error(f"MCP error: {err}")
                response = err.error
                # Also handle McpError responses
                if hasattr(response, 'isError'):
                    response.isError = False
            except Exception as err:
                logger.error(f"Exception: {err}")
                if raise_exceptions:
                    raise err
                response = types.ErrorData(code=0, message=str(err), data=None)
                # ErrorData doesn't have isError, but we can wrap it
                response = types.ServerResult(response)
                if hasattr(response.root, 'isError'):
                    response.root.isError = False
            finally:
                # Reset the global state after we are done
                if token is not None:
                    request_ctx.reset(token)

            await message.respond(response)
        else:
            # For method not found, also ensure it's not marked as error
            error_response = types.ErrorData(
                code=types.METHOD_NOT_FOUND,
                message="Method not found",
            )
            await message.respond(error_response)

        logger.debug("Response sent") 
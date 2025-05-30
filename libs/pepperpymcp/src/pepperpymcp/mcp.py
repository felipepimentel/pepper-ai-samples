"""
Core MCP server implementation and extensions.

This module provides extensions to the official MCP SDK, adding template support
and other utilities while ensuring strict adherence to the official implementation.
"""

import asyncio
import logging
import os
import signal
import sys
from enum import Enum
from typing import Any, Dict, List, Union

from mcp import types
from mcp.server import FastMCP as OfficialFastMCP

logger = logging.getLogger(__name__)


class ConnectionMode(Enum):
    """Connection mode for the MCP server."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


# Helper functions to create message content more easily
def TextContent(text: str) -> Dict[str, Any]:
    """Create text content without importing types directly."""
    return types.TextContent(type="text", text=text)


def AssistantRole(msg: str) -> Dict[str, Any]:
    """
    Create an assistant message with the given text.

    Args:
        msg: The message text

    Returns:
        A properly formatted assistant message object

    Example:
        ```python
        messages = [
            UserRole("Hello"),
            AssistantRole("Hi there! How can I help you today?")
        ]
        ```
    """
    return {"role": "assistant", "content": [{"type": "text", "text": msg}]}


def UserRole(msg: str) -> Dict[str, Any]:
    """
    Create a user message with the given text.

    Args:
        msg: The message text

    Returns:
        A properly formatted user message object

    Example:
        ```python
        messages = [
            UserRole("Can you help me with a coding question?")
        ]
        ```
    """
    return {"role": "user", "content": [{"type": "text", "text": msg}]}


def SystemRole(msg: str) -> Dict[str, Any]:
    """
    Create a system message with the given text.

    Args:
        msg: The message text

    Returns:
        A properly formatted system message object

    Example:
        ```python
        messages = [
            SystemRole("You are a helpful assistant"),
            UserRole("Hello")
        ]
        ```
    """
    return {"role": "system", "content": [{"type": "text", "text": msg}]}


# Add aliases for backward compatibility
def AssistantMessage(msg: str) -> Dict[str, Any]:
    """
    Create an assistant message with the given text.
    
    Deprecated: Use PepperFastMCP.create_assistant_message() instead.
    
    Args:
        msg: The message text
        
    Returns:
        A properly formatted assistant message object
    """
    import warnings
    warnings.warn(
        "AssistantMessage() is deprecated, use mcp.create_assistant_message() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return AssistantRole(msg)

def UserMessage(msg: str) -> Dict[str, Any]:
    """
    Create a user message with the given text.
    
    Deprecated: Use PepperFastMCP.create_user_message() instead.
    
    Args:
        msg: The message text
        
    Returns:
        A properly formatted user message object
    """
    import warnings
    warnings.warn(
        "UserMessage() is deprecated, use mcp.create_user_message() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return UserRole(msg)

def SystemMessage(msg: str) -> Dict[str, Any]:
    """
    Create a system message with the given text.
    
    Deprecated: Use PepperFastMCP.create_system_message() instead.
    
    Args:
        msg: The message text
        
    Returns:
        A properly formatted system message object
    """
    import warnings
    warnings.warn(
        "SystemMessage() is deprecated, use mcp.create_system_message() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return SystemRole(msg)


def CreateMessages(
    messages: List[Union[Dict[str, Any], str]], default_role: str = "user"
) -> List[Dict[str, Any]]:
    """
    Create a properly formatted list of messages for use with the MCP SDK.

    This function accepts either dictionaries (from AssistantRole, UserRole, etc.)
    or plain strings (which will use the default_role).

    Args:
        messages: List of messages (dicts or strings)
        default_role: Default role to use for string messages ("user", "assistant", or "system")

    Returns:
        A properly formatted list of messages

    Example:
        ```python
        # Mixed format
        messages = CreateMessages([
            SystemRole("You are a helpful assistant"),
            "Tell me about Python",  # Will be converted to UserRole
            AssistantRole("Python is a programming language...")
        ])
        ```
    """
    result = []

    for msg in messages:
        if isinstance(msg, str):
            if default_role == "user":
                result.append(UserRole(msg))
            elif default_role == "assistant":
                result.append(AssistantRole(msg))
            elif default_role == "system":
                result.append(SystemRole(msg))
            else:
                raise ValueError(f"Invalid default_role: {default_role}")
        elif isinstance(msg, dict):
            # Validate minimal structure
            if "role" not in msg or "content" not in msg:
                raise ValueError("Message dict must contain 'role' and 'content' keys")
            result.append(msg)
        else:
            raise TypeError(f"Expected str or dict, got {type(msg)}")

    return result


class PepperFastMCP:
    """
    Extended FastMCP implementation that adds template support.

    This is a wrapper around the official FastMCP class that adds
    template functionality while maintaining compatibility with the
    official SDK. It delegates all core functionality to the official
    implementation and only extends what's missing.
    """

    def __init__(self, name: str, description: str = "", **kwargs):
        """
        Initialize the extended FastMCP server.

        Args:
            name: Server name
            description: Server description
            **kwargs: Additional arguments passed to official FastMCP
        """
        # Create the official FastMCP instance
        self._mcp = OfficialFastMCP(name, description=description, **kwargs)

        # Template cache
        self._templates = {}
        self._template_paths = ["templates"]

        # Create messages namespace
        self.messages = MessagesNamespace(self)

        # For graceful shutdown
        self._shutdown_event = None
        self._server_task = None
        self._background_tasks = set()

    def __getattr__(self, name):
        """Delegate all attributes to the official FastMCP instance."""
        return getattr(self._mcp, name)

    def get_template(self, name: str) -> str:
        """
        Get a template by name from the templates directory.

        Args:
            name: The name of the template file without extension

        Returns:
            The template content as a string
        """
        # Check if template is already cached
        if name in self._templates:
            return self._templates[name]

        # Try to find the template in template paths
        template_content = None
        for path in self._template_paths:
            template_file = f"{path}/{name}.template"
            if os.path.exists(template_file):
                with open(template_file, "r", encoding="utf-8") as f:
                    template_content = f.read()
                break

        if template_content is None:
            raise FileNotFoundError(f"Template {name} not found in {self._template_paths}")

        # Cache the template
        self._templates[name] = template_content
        return template_content

    def add_template_path(self, path: str) -> None:
        """
        Add a path to search for templates.

        Args:
            path: Directory path to search for templates
        """
        if os.path.isdir(path) and path not in self._template_paths:
            self._template_paths.append(path)

    # Explicitly delegate key methods to the official FastMCP for clarity
    def tool(self, *args, **kwargs):
        """Register a tool using the official FastMCP."""
        return self._mcp.tool(*args, **kwargs)

    def resource(self, *args, **kwargs):
        """Register a resource using the official FastMCP."""
        return self._mcp.resource(*args, **kwargs)

    def prompt(self, *args, **kwargs):
        """Register a prompt using the official FastMCP."""
        return self._mcp.prompt(*args, **kwargs)

    def http_endpoint(self, path: str):
        """
        Register an HTTP endpoint.

        This is a custom extension not available in the official FastMCP class.
        It adds a route to the underlying FastAPI app.
        """
        # Import FastAPI here to avoid circular imports
        from fastapi import FastAPI

        # Create FastAPI app if it doesn't exist
        if not hasattr(self._mcp, "app"):
            self._mcp.app = FastAPI()

        # Return the route decorator
        return self._mcp.app.get(path)

    def sse_app(self):
        """
        Get the SSE app for mounting in an existing ASGI server.
        """
        if hasattr(self._mcp, "sse_app"):
            return self._mcp.sse_app()
        return getattr(self._mcp, "app", None)

    def configure_cors(self, origins=None):
        """
        Configure CORS for the server.
        """
        if origins is None:
            origins = ["*"]

        # Import CORS middleware here to avoid circular imports
        from fastapi.middleware.cors import CORSMiddleware

        app = getattr(self._mcp, "app", None)
        if app:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

    async def _handle_shutdown(self):
        """
        Handle server shutdown gracefully.

        This method is called when the server receives a shutdown signal.
        It properly closes the server and any background tasks.
        """
        logger.info("Shutting down MCP server gracefully...")

        # Cancel all background tasks
        if hasattr(self, "_background_tasks"):
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()

            # Wait for all tasks to complete with a timeout
            if self._background_tasks:
                try:
                    await asyncio.wait(self._background_tasks, timeout=3)
                except asyncio.TimeoutError:
                    logger.warning("Some tasks did not complete in time")

        # Close the server if it has a close method
        server = getattr(self._mcp, "server", None)
        if server and hasattr(server, "close"):
            logger.info("Closing server...")
            server.close()
            if hasattr(server, "wait_closed"):
                try:
                    await asyncio.wait_for(server.wait_closed(), timeout=2)
                except asyncio.TimeoutError:
                    logger.warning("Server did not close in time")

        logger.info("Server shutdown complete")

    def create_background_task(self, coro):
        """
        Create a background task that will be properly cleaned up on shutdown.

        Args:
            coro: Coroutine to run as a background task

        Returns:
            The created task
        """
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    async def _run_server_with_graceful_shutdown(self, *args, **kwargs):
        """
        Run the server with graceful shutdown support.

        This method handles signals for graceful shutdown and ensures
        all resources are properly cleaned up when the server exits.
        """
        self._shutdown_event = asyncio.Event()

        # Get the current loop
        loop = asyncio.get_running_loop()

        # Set up signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            # Use a callback that creates a task properly
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._signal_handler(s)))

        try:
            # Run server in a task so we can cancel it
            self._server_task = asyncio.create_task(self._run_async(*args, **kwargs))

            # Create a task for the shutdown event
            shutdown_wait_task = asyncio.create_task(self._shutdown_event.wait())

            # Wait for shutdown event or server completion
            done, pending = await asyncio.wait(
                [shutdown_wait_task, self._server_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # If shutdown event was triggered, clean up
            if shutdown_wait_task in done and self._server_task in pending:
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass

            # Handle server task result or exception
            if self._server_task in done:
                result = self._server_task.result()
                return result

        finally:
            # Clean up
            await self._handle_shutdown()

            # Remove signal handlers
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.remove_signal_handler(sig)

    async def _signal_handler(self, sig):
        """
        Handle shutdown signals.

        Args:
            sig: Signal number
        """
        if not self._shutdown_event.is_set():
            logger.info(f"Received shutdown signal {sig.name}")
            self._shutdown_event.set()

            # Force exit after 5 seconds if graceful shutdown fails
            loop = asyncio.get_running_loop()
            loop.call_later(5, lambda: os._exit(0))

    async def _run_async(self, *args, **kwargs):
        """Run the server asynchronously."""
        logger.info(f"Starting MCP server: {self._mcp.name}")

        # Check if we're being run in stdio mode
        if "--stdio" in sys.argv and not kwargs.get("stdio"):
            try:
                # Try to use the run_stdio_async method if available
                if hasattr(self._mcp, "run_stdio_async"):
                    return await self._mcp.run_stdio_async()

                # Fall back to the run method with stdio=True
                return await self._mcp.run(stdio=True)
            except asyncio.CancelledError:
                logger.info("Server task cancelled")
                raise
            except AttributeError:
                # If both fail, try the standard run method
                return await self._mcp.run(*args, **kwargs)

        # Use the regular run method
        try:
            return await self._mcp.run(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info("Server task cancelled")
            raise

    async def _run_stdio(self):
        """Run the server in stdio mode."""
        logger.info(f"Running {self._mcp.name} in stdio mode")
        
        # Initialize shutdown event
        self._shutdown_event = asyncio.Event()
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._stdio_signal_handler(s)))
        
        server_task = None
        try:
            # Start server task
            # Try to use the run_stdio_async method if available
            if hasattr(self._mcp, "run_stdio_async"):
                server_task = asyncio.create_task(self._mcp.run_stdio_async())
            else:
                # Fall back to the run method with stdio=True
                server_task = asyncio.create_task(self._mcp.run(stdio=True))
            
            # Wait for either shutdown event or server task completion
            shutdown_task = asyncio.create_task(self._shutdown_event.wait())
            done, pending = await asyncio.wait(
                [shutdown_task, server_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel server task if shutdown was triggered
            if server_task in pending:
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    logger.info("Server task cancelled")
            
            # If shutdown was triggered directly, allow exit
            if shutdown_task in done:
                return  # Let the finally block run, then exit
            
        except asyncio.CancelledError:
            logger.info("Server task cancelled")
            if server_task and not server_task.done():
                server_task.cancel()
        except Exception as e:
            logger.error(f"Error running stdio server: {str(e)}")
            raise
        finally:
            # Clean up signal handlers
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.remove_signal_handler(sig)
                except Exception:
                    pass
            
            # Perform cleanup
            await self._handle_shutdown()
            
            # Explicitly release stdin/stdout references
            try:
                sys.stdout.flush()
                sys.stderr.flush()
            except Exception:
                pass

    async def _stdio_signal_handler(self, sig):
        """Handle signals for stdio mode gracefully.
        
        Args:
            sig: Signal number
        """
        if not self._shutdown_event.is_set():
            logger.info(f"Received signal {sig.name}, initiating shutdown")
            self._shutdown_event.set()
            
            # Give tasks a chance to clean up
            await asyncio.sleep(0.5)
            
            # Instead of sys.exit(), just let the event finish naturally
            if sig == signal.SIGINT:
                logger.info("Exiting due to keyboard interrupt")
                # Force exit after cleanup is complete (in 0.5 sec)
                loop = asyncio.get_running_loop()
                loop.call_later(1.0, lambda: os._exit(0))

    def run(self, *args, **kwargs):
        """
        Run the server with UV-compatible approach.
        
        This method detects the appropriate mode (stdio or HTTP) and runs the server accordingly.
        The method handles signals for graceful shutdown and ensures all resources are 
        properly cleaned up when the server exits.
        
        Args:
            *args: Positional arguments passed to the underlying server
            **kwargs: Keyword arguments including:
                - stdio: Force stdio mode
                - host: Host address for HTTP server (default: "0.0.0.0")
                - port: Port for HTTP server (default: 8000)
                - log_level: Logging level (default: "info")
        
        Returns:
            None
        """
        # Determine if we should run in stdio mode
        use_stdio = kwargs.get("stdio", False) or "--stdio" in sys.argv
        
        if use_stdio:
            print(f"Starting {self._mcp.name} MCP Server in stdio mode")
            try:
                # Using asyncio.run with debug=False helps with proper cleanup
                asyncio.run(self._run_stdio(), debug=False)
                
                # Force exit if we somehow get here without exiting
                os._exit(0)
            except KeyboardInterrupt:
                # This should not usually happen because of our signal handler
                logger.info("Keyboard interrupt received, forcing exit")
                os._exit(0)
            except asyncio.CancelledError:
                logger.info("Asyncio task cancelled, forcing exit")
                os._exit(0)
            except Exception as e:
                logger.error(f"Error in stdio mode: {str(e)}")
                # Reraise only if it's not a controlled exit
                if not isinstance(e, SystemExit):
                    raise
                os._exit(0)
            finally:
                # Final cleanup for UV compatibility
                sys.stdout.flush()
                sys.stderr.flush()
                os._exit(0)  # Last resort exit
        else:
            import uvicorn
            
            print(f"Starting {self._mcp.name} MCP Server in HTTP mode")
            
            # Initialize shutdown event
            self._shutdown_event = asyncio.Event()
            
            async def run_server():
                config = uvicorn.Config(
                    app=self._mcp.app, 
                    host=kwargs.get("host", "0.0.0.0"), 
                    port=kwargs.get("port", 8000), 
                    log_level=kwargs.get("log_level", "info")
                )
                server = uvicorn.Server(config)
                try:
                    await server.serve()
                except asyncio.CancelledError:
                    logger.info("Server task cancelled")
                finally:
                    # Set shutdown event and handle cleanup
                    if hasattr(self, "_shutdown_event"):
                        self._shutdown_event.set()
                    await self._handle_shutdown()
            
            try:
                # Run with direct asyncio call - always use this approach for UV compatibility
                return asyncio.run(run_server())
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down")
                return None
            except Exception as e:
                logger.error(f"Error running server: {str(e)}")
                raise
    
    # Context manager support for graceful shutdown
    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with graceful shutdown."""
        await self._handle_shutdown()
        return False

    # Image handling
    def create_image(self, data: bytes, format: str = "png") -> Dict[str, Any]:
        """Create an image content object for messages."""
        if hasattr(self._mcp, "create_image"):
            return self._mcp.create_image(data, format)

        # Fall back to our own implementation
        return types.ImageContent(
            type="image",
            source=f"data:image/{format};base64,{data.decode('utf-8') if isinstance(data, bytes) else data}",
        )

    # Message creation helper methods
    def create_text_content(self, text: str) -> Dict[str, Any]:
        """
        Create text content for a message.

        Args:
            text: The text content

        Returns:
            A properly formatted text content object
        """
        return TextContent(text)

    def create_assistant_message(self, content: str) -> Dict[str, Any]:
        """
        Create an assistant message with the given text.

        Args:
            content: The message text

        Returns:
            A properly formatted assistant message object
        """
        return AssistantRole(content)

    def create_user_message(self, content: str) -> Dict[str, Any]:
        """
        Create a user message with the given text.

        Args:
            content: The message text

        Returns:
            A properly formatted user message object
        """
        return UserRole(content)

    def create_system_message(self, content: str) -> Dict[str, Any]:
        """
        Create a system message with the given text.

        Args:
            content: The message text

        Returns:
            A properly formatted system message object
        """
        return SystemRole(content)

    def create_messages(
        self, messages: List[Union[Dict[str, Any], str]], default_role: str = "user"
    ) -> List[Dict[str, Any]]:
        """
        Create a properly formatted list of messages.

        Args:
            messages: List of messages (dicts or strings)
            default_role: Default role to use for string messages

        Returns:
            A properly formatted list of messages
        """
        return CreateMessages(messages, default_role)


class MessagesNamespace:
    """Namespace for message creation methods."""

    def __init__(self, mcp_instance):
        self._mcp = mcp_instance

    def text(self, content: str) -> Dict[str, Any]:
        """Create text content."""
        return self._mcp.create_text_content(content)

    def assistant(self, content: str) -> Dict[str, Any]:
        """Create an assistant message."""
        return self._mcp.create_assistant_message(content)

    def user(self, content: str) -> Dict[str, Any]:
        """Create a user message."""
        return self._mcp.create_user_message(content)

    def system(self, content: str) -> Dict[str, Any]:
        """Create a system message."""
        return self._mcp.create_system_message(content)

    def create_list(
        self, messages: List[Union[Dict[str, Any], str]], default_role: str = "user"
    ) -> List[Dict[str, Any]]:
        """Create a list of messages."""
        return self._mcp.create_messages(messages, default_role)


# Factory function to create the appropriate MCP server
def create_mcp_server(name: str, description: str = "", **kwargs):
    """
    Factory function to create an MCP server instance.

    Args:
        name: Server name
        description: Server description
        **kwargs: Additional arguments to pass to the server constructor

    Returns:
        An MCP server instance
    """
    return PepperFastMCP(name, description=description, **kwargs)

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ToolResult:
    """Result returned by a tool execution."""

    def __init__(
        self,
        name: str,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
    ) -> None:
        self.name = name
        self.success = success
        self.data = data
        self.error = error

    def model_dump(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }


class ToolBase(ABC):
    """Abstract base class for all CodeForge AI tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool's unique name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description of the tool."""

    @property
    @abstractmethod
    def input_schema(self) -> dict:
        """Return the Pydantic- compatible input schema for this tool."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given keyword arguments."""

    def run(self, **kwargs: Any) -> ToolResult:
        """Synchronous entry point; wraps the async execute."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        return loop.run_until_complete(self.execute(**kwargs))
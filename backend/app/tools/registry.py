from __future__ import annotations

from typing import Dict, List, Optional

from .base import ToolBase, ToolResult


class ToolRegistry:
    """Registry for discovering and looking up available tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolBase]:
        """Get a tool by name, or None if not found."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """Return a list of registered tool names."""
        return list(self._tools.keys())

    def execute_tool(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name with the given keyword arguments.

        Returns a ToolResult instance.
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                name=name,
                success=False,
                error=f"Unknown tool: {name}",
            )
        return tool.execute(**kwargs)
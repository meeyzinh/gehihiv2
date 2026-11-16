"""
Xiaozhi MCP Portal - Package Initialization
Cổng kết nối 78 công cụ MCP mở rộng trí tuệ AI cho Robot Xiaozhi
"""

from .tools_engine import (
    execute_tool,
    get_all_tools_metadata,
    get_tool_schemas,
    toggle_tool,
    get_tool_states,
    TOTAL_TOOLS_COUNT
)
from .mcp_bridge import mcp_device_manager

__all__ = [
    "execute_tool",
    "get_all_tools_metadata",
    "get_tool_schemas",
    "toggle_tool",
    "get_tool_states",
    "TOTAL_TOOLS_COUNT",
    "mcp_device_manager"
]

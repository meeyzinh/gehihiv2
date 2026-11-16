"""
Xiaozhi MCP Portal - Package Initialization
Cổng kết nối 78 công cụ MCP mở rộng trí tuệ AI cho Hệ thống Đa Robot Xiaozhi
"""

from .tools_engine import (
    execute_tool,
    get_all_tools_metadata,
    get_tool_schemas,
    get_tool_schemas_for_device,
    toggle_tool,
    get_tool_states,
    get_robot_permissions,
    set_robot_permissions,
    toggle_robot_group,
    toggle_robot_tool,
    save_robot_memory,
    get_robot_memories,
    delete_robot_memory,
    save_robot_task,
    get_robot_tasks,
    MCP_TOOL_GROUPS,
    TOTAL_TOOLS_COUNT
)
from .mcp_bridge import (
    mcp_device_manager,
    MCPConnectionManager,
    MCPConnectionPool
)

__all__ = [
    "execute_tool",
    "get_all_tools_metadata",
    "get_tool_schemas",
    "get_tool_schemas_for_device",
    "toggle_tool",
    "get_tool_states",
    "get_robot_permissions",
    "set_robot_permissions",
    "toggle_robot_group",
    "toggle_robot_tool",
    "save_robot_memory",
    "get_robot_memories",
    "delete_robot_memory",
    "save_robot_task",
    "get_robot_tasks",
    "MCP_TOOL_GROUPS",
    "TOTAL_TOOLS_COUNT",
    "mcp_device_manager",
    "MCPConnectionManager",
    "MCPConnectionPool"
]

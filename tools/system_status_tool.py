# tools/system_status_tool.py - System Status Tool

import logging
import os
import psutil
from typing import Any, Dict
from datetime import datetime
from mcp import Tool

from config import Config

logger = logging.getLogger(__name__)


class SystemStatusTool(Tool):
    """MCP tool for system status and health monitoring"""

    def __init__(self):
        super().__init__(
            name="system_status",
            description="Get YouTube Intelligence MCP Server system status and health metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_detailed": {
                        "type": "boolean",
                        "description": "Include detailed system metrics",
                        "default": False
                    }
                }
            }
        )

    async def call(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get system status"""
        try:
            include_detailed = arguments.get("include_detailed", False)

            # Basic system info
            status = {
                "server_name": Config.MCP_SERVER_NAME,
                "version": Config.MCP_SERVER_VERSION,
                "timestamp": datetime.utcnow().isoformat() + 'Z',  # Fixed timestamp format
                "status": "healthy",
                "uptime_seconds": self._get_uptime(),
                "configuration": {
                    "youtube_api_configured": bool(Config.YOUTUBE_API_KEY),
                    "firebase_configured": bool(Config.FIREBASE_PROJECT_ID),
                    "claude_api_configured": bool(Config.ANTHROPIC_API_KEY),
                    "output_directory": str(Config.OUTPUT_DIR),
                    "max_videos_per_search": Config.MAX_VIDEOS_PER_SEARCH
                }
            }

            # Add detailed metrics if requested
            if include_detailed:
                status["system_metrics"] = self._get_system_metrics()
                status["api_status"] = self._check_api_status()

            return {
                "success": True,
                "status": status
            }

        except Exception as e:
            logger.error(f"System status error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get system status"
            }

    def _get_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            return psutil.boot_time()
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return 0.0

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids()),
                "network_connections": len(psutil.net_connections())
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": "Unable to retrieve system metrics"}

    def _check_api_status(self) -> Dict[str, str]:
        """Check API configuration status"""
        return {
            "youtube_api": "configured" if Config.YOUTUBE_API_KEY else "not_configured",
            "firebase": "configured" if Config.FIREBASE_PROJECT_ID else "not_configured",
            "claude_api": "configured" if Config.ANTHROPIC_API_KEY else "not_configured"
        }

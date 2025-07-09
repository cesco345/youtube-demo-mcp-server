# mcp_server.py - Main MCP Server Implementation with Proper Initialization

import asyncio
import logging
from typing import Any, Dict, List, Optional

# Correct imports for MCP Server
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import ServerCapabilities, ToolsCapability
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

from config import Config
from tools.video_search_tool import VideoSearchTool
from tools.market_analysis_tool import MarketAnalysisTool
from tools.system_status_tool import SystemStatusTool

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main MCP server instance
server = Server(Config.MCP_SERVER_NAME, Config.MCP_SERVER_VERSION)

# Initialize tools
youtube_tools = {
    'search_videos': VideoSearchTool(),
    'analyze_market': MarketAnalysisTool(),
    'system_status': SystemStatusTool()
}

# Track initialization state
_server_initialized = False

logger.info(f"Initialized {len(youtube_tools)} MCP tools")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    try:
        # Check if server is initialized
        if not _server_initialized:
            logger.warning(
                "Tools requested before server initialization complete")
            return []

        tools_list = []
        for tool_name, tool_instance in youtube_tools.items():
            mcp_tool = Tool(
                name=tool_instance.name,
                description=tool_instance.description,
                inputSchema=tool_instance.inputSchema
            )
            tools_list.append(mcp_tool)

        logger.info(f"Listed {len(tools_list)} available tools")
        return tools_list

    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return []


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute MCP tool calls"""
    try:
        # Check if server is initialized
        if not _server_initialized:
            error_msg = "Server not yet initialized. Please wait for initialization to complete."
            logger.warning(f"Tool call rejected - {error_msg}")
            return [TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]

        logger.info(f"Tool call: {name} with arguments: {arguments}")

        # Find and execute tool
        if name not in youtube_tools:
            error_msg = f"Tool '{name}' not found. Available tools: {list(youtube_tools.keys())}"
            logger.error(error_msg)
            return [TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]

        # Execute tool
        tool_instance = youtube_tools[name]
        result = await tool_instance.call(arguments)

        # Format response
        if result.get('success', False):
            response_text = format_tool_response(name, result)
        else:
            response_text = f"Tool execution failed: {result.get('message', 'Unknown error')}"

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        error_msg = f"Error executing tool '{name}': {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]


def format_tool_response(tool_name: str, result: Dict[str, Any]) -> str:
    """Format tool response for display"""
    try:
        if tool_name == 'search_videos':
            return format_video_search_response(result)
        elif tool_name == 'analyze_market':
            return format_market_analysis_response(result)
        elif tool_name == 'system_status':
            return format_system_status_response(result)
        else:
            return f"Results from {tool_name}:\n{str(result)}"

    except Exception as e:
        logger.error(f"Error formatting response: {e}")
        return f"Tool executed successfully but response formatting failed: {str(result)}"


def format_video_search_response(result: Dict[str, Any]) -> str:
    """Format video search results"""
    response = []
    response.append(f"**YouTube Video Search Results**")
    response.append(f"Query: {result.get('query', 'Unknown')}")
    response.append(f"Found: {result.get('videos_found', 0)} videos")
    response.append(
        f"Average Engagement: {result.get('average_engagement', 'N/A')}")
    response.append("")

    videos = result.get('videos', [])
    for i, video in enumerate(videos[:10], 1):  # Show top 10
        response.append(f"{i}. **{video['title']}**")
        response.append(f"   Channel: {video['channel']}")
        response.append(
            f"   Views: {video['views']:,} | Likes: {video['likes']:,} | Comments: {video['comments']:,}")
        response.append(
            f"   Engagement: {video['engagement_rate']} | Published: {video['published']}")
        response.append(
            f"   Duration: {video['duration']} | Category: {video['category']}")
        response.append(f"   URL: {video['url']}")
        response.append("")

    return "\n".join(response)


def format_market_analysis_response(result: Dict[str, Any]) -> str:
    """Format market analysis results"""
    response = []
    response.append(f"**Market Analysis Results**")
    response.append(f"Topic: {result.get('topic', 'Unknown')}")
    response.append(f"Videos Analyzed: {result.get('videos_analyzed', 0)}")
    response.append(f"Timeframe: {result.get('timeframe_days', 0)} days")
    response.append("")

    analysis = result.get('analysis', {})

    # Market Overview
    overview = analysis.get('market_overview', {})
    response.append("**Market Overview**")
    response.append(f"• Total Views: {overview.get('total_views', 0):,}")
    response.append(f"• Average Views: {overview.get('average_views', 0):,}")
    response.append(
        f"• Average Engagement: {overview.get('average_engagement_rate', 'N/A')}")
    response.append(f"• Unique Creators: {overview.get('unique_creators', 0)}")
    response.append(
        f"• Competition Level: {overview.get('competition_level', 'Unknown')}")
    response.append(
        f"• Market Sentiment: {overview.get('market_sentiment', 'N/A')}")
    response.append("")

    # Top Videos
    top_videos = analysis.get('top_performing_videos', [])
    if top_videos:
        response.append("**Top Performing Videos**")
        for i, video in enumerate(top_videos[:5], 1):
            response.append(
                f"{i}. {video['title']} - {video['views']:,} views ({video['channel']})")
        response.append("")

    # Top Channels
    top_channels = analysis.get('top_channels', [])
    if top_channels:
        response.append("**Top Channels**")
        for i, channel in enumerate(top_channels[:5], 1):
            response.append(
                f"{i}. {channel['channel']} - {channel['total_views']:,} total views ({channel['video_count']} videos)")
        response.append("")

    # Insights
    insights = analysis.get('insights', [])
    if insights:
        response.append("**Key Insights**")
        for insight in insights:
            response.append(f"• {insight}")

    return "\n".join(response)


def format_system_status_response(result: Dict[str, Any]) -> str:
    """Format system status results"""
    response = []
    status = result.get('status', {})

    response.append(
        f"⚡ **{status.get('server_name', 'YouTube Intelligence')} System Status**")
    response.append(f"Version: {status.get('version', 'Unknown')}")
    response.append(f"Status: {status.get('status', 'Unknown')}")
    response.append(f"Timestamp: {status.get('timestamp', 'Unknown')}")
    response.append("")

    # Configuration
    config = status.get('configuration', {})
    response.append("**🔧 Configuration**")
    response.append(
        f"• YouTube API: {'Configured' if config.get('youtube_api_configured') else 'Not Configured'}")
    response.append(
        f"• Firebase: {'Configured' if config.get('firebase_configured') else 'Not Configured'}")
    response.append(
        f"• Claude API: {'Configured' if config.get('claude_api_configured') else 'Not Configured'}")
    response.append(
        f"• Max Videos Per Search: {config.get('max_videos_per_search', 'Unknown')}")
    response.append("")

    # System Metrics (if available)
    metrics = status.get('system_metrics', {})
    if metrics and 'error' not in metrics:
        response.append("**📊 System Metrics**")
        response.append(
            f"• CPU Usage: {metrics.get('cpu_percent', 'Unknown')}%")
        response.append(
            f"• Memory Usage: {metrics.get('memory_percent', 'Unknown')}%")
        response.append(
            f"• Disk Usage: {metrics.get('disk_usage_percent', 'Unknown')}%")

    return "\n".join(response)


async def initialize_server():
    """Initialize server components"""
    global _server_initialized

    try:
        logger.info("Initializing YouTube Intelligence MCP Server")

        # Validate configuration
        Config.validate_config()
        logger.info("Configuration validated successfully")

        # Initialize tools (already done above, but verify they're working)
        for tool_name, tool_instance in youtube_tools.items():
            logger.debug(
                f"Tool '{tool_name}' initialized: {tool_instance.name}")

        # Mark server as initialized
        _server_initialized = True
        logger.info("Server initialization complete")

    except Exception as e:
        logger.error(f"Server initialization failed: {e}")
        raise


async def main():
    """Main entry point for the MCP server"""
    try:
        # Initialize server first
        await initialize_server()

        # Create server capabilities
        capabilities = ServerCapabilities(tools=ToolsCapability())

        # Create initialization options
        init_options = InitializationOptions(
            server_name=Config.MCP_SERVER_NAME,
            server_version=Config.MCP_SERVER_VERSION,
            capabilities=capabilities
        )

        logger.info(
            f"Starting {Config.MCP_SERVER_NAME} v{Config.MCP_SERVER_VERSION}")

        # Run stdio server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, init_options)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

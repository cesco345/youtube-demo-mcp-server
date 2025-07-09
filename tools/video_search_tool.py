# tools/video_search_tool.py - MCP Video Search Tool

import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta
from mcp import Tool

from services.youtube_service import YouTubeService
from models.youtube_models import SearchQuery

logger = logging.getLogger(__name__)


class VideoSearchTool(Tool):
    """MCP tool for searching YouTube videos"""

    def __init__(self):
        super().__init__(
            name="search_videos",
            description="Search YouTube videos with detailed analysis and insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for YouTube videos"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order: relevance, date, rating, viewCount",
                        "default": "relevance"
                    },
                    "region_code": {
                        "type": "string",
                        "description": "Region code for localized results (default: US)",
                        "default": "US"
                    },
                    "published_after_days": {
                        "type": "integer",
                        "description": "Filter videos published within last N days (optional)",
                        "default": None
                    }
                },
                "required": ["query"]
            }
        )
        self.youtube_service = YouTubeService()

    async def call(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute video search"""
        try:
            # Extract parameters
            query_text = arguments.get("query", "")
            max_results = min(arguments.get("max_results", 10), 50)
            order = arguments.get("order", "relevance")
            region_code = arguments.get("region_code", "US")
            published_after_days = arguments.get("published_after_days", None)

            logger.info(f"Searching videos: {query_text}")

            # Create search query with optional date filter
            search_query_params = {
                "query": query_text,
                "max_results": max_results,
                "order": order,
                "region_code": region_code
            }

            # Add date filter if specified
            if published_after_days is not None:
                search_query_params["published_after"] = self._format_youtube_timestamp(
                    published_after_days)

            search_query = SearchQuery(**search_query_params)

            # Execute search
            results = self.youtube_service.search_videos(search_query)

            # Format results for MCP response
            response = {
                "success": True,
                "query": query_text,
                "total_results": results.total_results,
                "videos_found": len(results.videos),
                "average_engagement": f"{results.average_engagement:.2%}",
                "search_parameters": {
                    "order": order,
                    "region_code": region_code,
                    "max_results": max_results,
                    "published_after_days": published_after_days
                },
                "videos": []
            }

            # Add video details
            for video in results.videos:
                video_data = {
                    "title": video.title,
                    "channel": video.channel_title,
                    "views": video.stats.view_count,
                    "likes": video.stats.like_count,
                    "comments": video.stats.comment_count,
                    "engagement_rate": f"{video.stats.engagement_rate:.2%}",
                    "published": video.published_at.strftime("%Y-%m-%d"),
                    "duration": video.duration,
                    "category": video.category.value,
                    "url": f"https://youtube.com/watch?v={video.video_id}",
                    "description_snippet": getattr(video, 'description_snippet', '')[:200] + '...' if hasattr(video, 'description_snippet') and len(getattr(video, 'description_snippet', '')) > 200 else getattr(video, 'description_snippet', '')
                }
                response["videos"].append(video_data)

            return response

        except Exception as e:
            logger.error(f"Video search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to search videos"
            }

    def _format_youtube_timestamp(self, days_ago: int = 30) -> str:
        """
        Format timestamp for YouTube API with proper timezone

        Args:
            days_ago: Number of days ago from now

        Returns:
            Properly formatted timestamp string for YouTube API
        """
        # Calculate the date X days ago using UTC
        past_date = datetime.utcnow() - timedelta(days=days_ago)

        # Format as ISO string with 'Z' timezone indicator
        # YouTube API requires either 'Z' or a valid timezone offset
        return past_date.isoformat() + 'Z'

    def get_tool_schema(self) -> Dict[str, Any]:
        """Return the complete tool schema for MCP registration"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }

# tools/market_analysis_tool.py - Market Analysis Tool

import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta
from mcp import Tool
import pandas as pd
from textblob import TextBlob

from services.youtube_service import YouTubeService
from models.youtube_models import SearchQuery

logger = logging.getLogger(__name__)


class MarketAnalysisTool(Tool):
    """MCP tool for YouTube market analysis and trends"""

    def __init__(self):
        super().__init__(
            name="analyze_market",
            description="Analyze YouTube market trends and competition for specific topics",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic or niche to analyze"
                    },
                    "timeframe_days": {
                        "type": "integer",
                        "description": "Analyze videos from last N days (default: 30)",
                        "default": 30
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "Number of videos to analyze (default: 50)",
                        "default": 50
                    }
                },
                "required": ["topic"]
            }
        )
        self.youtube_service = YouTubeService()

    async def call(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market analysis"""
        try:
            topic = arguments.get("topic", "")
            timeframe_days = arguments.get("timeframe_days", 30)
            sample_size = min(arguments.get("sample_size", 50), 100)

            logger.info(f"Analyzing market for topic: {topic}")

            # Search for recent videos with proper timestamp formatting
            published_after = self._format_youtube_timestamp(timeframe_days)
            search_query = SearchQuery(
                query=topic,
                max_results=sample_size,
                published_after=published_after,
                order="viewCount"
            )

            results = self.youtube_service.search_videos(search_query)

            if not results.videos:
                return {
                    "success": False,
                    "message": f"No videos found for topic: {topic}"
                }

            # Analyze market metrics
            analysis = self._analyze_market_data(results.videos, topic)

            return {
                "success": True,
                "topic": topic,
                "timeframe_days": timeframe_days,
                "videos_analyzed": len(results.videos),
                "analysis": analysis
            }

        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze market"
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

    def _analyze_market_data(self, videos, topic):
        """Analyze market data and generate insights"""
        # Convert to DataFrame for analysis
        data = []
        for video in videos:
            data.append({
                'title': video.title,
                'views': video.stats.view_count,
                'likes': video.stats.like_count,
                'comments': video.stats.comment_count,
                'engagement_rate': video.stats.engagement_rate,
                'channel': video.channel_title,
                'published': video.published_at,
                'duration_seconds': video.stats.duration_seconds
            })

        df = pd.DataFrame(data)

        # Calculate market metrics
        total_views = df['views'].sum()
        avg_views = df['views'].mean()
        avg_engagement = df['engagement_rate'].mean()

        # Find top performers
        top_videos = df.nlargest(5, 'views')[
            ['title', 'views', 'channel']].to_dict('records')

        # Channel analysis
        channel_performance = df.groupby('channel').agg({
            'views': ['sum', 'mean', 'count'],
            'engagement_rate': 'mean'
        }).round(2)

        top_channels = channel_performance.nlargest(5, ('views', 'sum'))

        # Sentiment analysis on titles
        sentiments = [
            TextBlob(title).sentiment.polarity for title in df['title']]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

        # Competition analysis
        unique_channels = df['channel'].nunique()
        competition_level = "High" if unique_channels > 30 else "Medium" if unique_channels > 15 else "Low"

        return {
            "market_overview": {
                "total_views": int(total_views),
                "average_views": int(avg_views),
                "average_engagement_rate": f"{avg_engagement:.2%}",
                "unique_creators": unique_channels,
                "competition_level": competition_level,
                "market_sentiment": f"{avg_sentiment:.2f}"
            },
            "top_performing_videos": top_videos,
            "top_channels": [
                {
                    "channel": idx,
                    "total_views": int(row[('views', 'sum')]),
                    "avg_views": int(row[('views', 'mean')]),
                    "video_count": int(row[('views', 'count')]),
                    "avg_engagement": f"{row[('engagement_rate', 'mean')]:.2%}"
                }
                for idx, row in top_channels.head(5).iterrows()
            ],
            "insights": self._generate_market_insights(df, topic, competition_level)
        }

    def _generate_market_insights(self, df, topic, competition_level):
        """Generate actionable market insights"""
        insights = []

        # View distribution insight
        views_std = df['views'].std()
        views_mean = df['views'].mean()
        if views_std > views_mean:
            insights.append(
                "High variance in video performance - opportunity for viral content")

        # Engagement insight
        high_engagement = df[df['engagement_rate'] > 0.05]
        if len(high_engagement) > 0:
            avg_duration = high_engagement['duration_seconds'].mean()
            insights.append(
                f"High-engagement videos average {int(avg_duration/60)} minutes duration")

        # Competition insight
        if competition_level == "Low":
            insights.append(
                "Low competition - good opportunity to establish authority")
        elif competition_level == "High":
            insights.append(
                "High competition - focus on unique angle or underserved subtopics")

        # Upload timing insight
        try:
            # Make the comparison datetime timezone-aware to match the data
            from datetime import timezone
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

            # Convert published dates to datetime if they're strings
            if not df.empty and not pd.api.types.is_datetime64_any_dtype(df['published']):
                df['published'] = pd.to_datetime(df['published'], utc=True)

            # Ensure published column is timezone-aware
            if not df.empty and df['published'].dt.tz is None:
                df['published'] = df['published'].dt.tz_localize('UTC')

            recent_videos = df[df['published'] > cutoff_date]
            if len(recent_videos) > len(df) * 0.3:
                insights.append(
                    "High recent activity - trending topic with immediate opportunity")
        except Exception as e:
            logger.warning(f"Could not analyze upload timing: {e}")
            # Skip this insight if there are datetime issues

        return insights

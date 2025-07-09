# models/youtube_models.py - YouTube Data Structures
# Data Models & Architecture
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class VideoCategory(str, Enum):
    """YouTube video categories"""
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    TECHNOLOGY = "technology"
    GAMING = "gaming"
    MUSIC = "music"
    NEWS = "news" 
    SPORTS = "sports"
    OTHER = "other"


class VideoStats(BaseModel):
    """Video statistics and metrics"""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    duration_seconds: int = 0

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate (likes + comments) / views"""
        if self.view_count == 0:
            return 0.0
        return (self.like_count + self.comment_count) / self.view_count


class VideoData(BaseModel):
    """Complete video data structure"""
    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    published_at: datetime
    duration: str
    category: VideoCategory = VideoCategory.OTHER
    stats: VideoStats
    tags: List[str] = []
    thumbnail_url: Optional[str] = None

    # Analysis fields
    sentiment_score: Optional[float] = None
    credibility_score: Optional[float] = None
    trending_score: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChannelData(BaseModel):
    """YouTube channel information"""
    channel_id: str
    title: str
    description: str
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    created_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None

    # Analysis fields
    authority_score: Optional[float] = None
    consistency_score: Optional[float] = None


class SearchQuery(BaseModel):
    """YouTube search query parameters"""
    query: str
    max_results: int = 25
    region_code: str = "US"
    language: str = "en"
    published_after: Optional[datetime] = None
    published_before: Optional[datetime] = None
    order: str = "relevance"  # relevance, date, rating, viewCount


class SearchResult(BaseModel):
    """YouTube search results"""
    query: SearchQuery
    videos: List[VideoData]
    total_results: int
    search_time: datetime = Field(default_factory=datetime.now)

    @property
    def average_engagement(self) -> float:
        """Calculate average engagement rate across all videos"""
        if not self.videos:
            return 0.0
        return sum(video.stats.engagement_rate for video in self.videos) / len(self.videos)


class MarketTrend(BaseModel):
    """Market trend analysis data"""
    keyword: str
    trend_score: float
    growth_rate: float
    competition_level: str  # low, medium, high
    related_topics: List[str] = []
    analysis_date: datetime = Field(default_factory=datetime.now)


class MarketAnalysis(BaseModel):
    """Complete market analysis results"""
    query: str
    trends: List[MarketTrend]
    top_performers: List[VideoData]
    market_insights: Dict[str, Any] = {}
    analysis_summary: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


# Example usage and validation
if __name__ == "__main__":
    # Create sample video data
    sample_video = VideoData(
        video_id="sample123",
        title="How to Build YouTube Intelligence AI",
        description="A comprehensive tutorial on building AI systems",
        channel_id="channel123",
        channel_title="Tech Tutorials",
        published_at=datetime.now(),
        duration="PT15M30S",
        category=VideoCategory.EDUCATION,
        stats=VideoStats(
            view_count=10000,
            like_count=500,
            comment_count=100,
            duration_seconds=930
        ),
        tags=["AI", "YouTube", "Tutorial", "Programming"]
    )

    print("Sample Video Data:")
    print(f"Title: {sample_video.title}")
    print(f"Engagement Rate: {sample_video.stats.engagement_rate:.2%}")
    print(f"JSON: {sample_video.json(indent=2)}")

    # Validate model
    print("\n✅ Video data model validation successful!")

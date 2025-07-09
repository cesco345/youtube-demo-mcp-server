# services/youtube_service.py - YouTube API Integration
# YouTube Service Integration

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate

from config import Config
from models.youtube_models import VideoData, ChannelData, SearchQuery, SearchResult, VideoStats, VideoCategory

logger = logging.getLogger(__name__)


class YouTubeService:
    """YouTube Data API service for video and channel operations"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YouTube API key is required")

        self.youtube = build(
            Config.YOUTUBE_API_SERVICE_NAME,
            Config.YOUTUBE_API_VERSION,
            developerKey=self.api_key
        )

        logger.info("YouTube service initialized successfully")

    def search_videos(self, query: SearchQuery) -> SearchResult:
        """Search for videos using YouTube Data API"""
        try:
            logger.info(f"Searching videos for query: {query.query}")

            # Build search parameters
            search_params = {
                'part': 'snippet',
                'q': query.query,
                'type': 'video',
                'maxResults': min(query.max_results, 50),  # API limit
                'regionCode': query.region_code,
                'relevanceLanguage': query.language,
                'order': query.order
            }

            # Add date filters if specified
            if query.published_after:
                search_params['publishedAfter'] = query.published_after.isoformat()
            if query.published_before:
                search_params['publishedBefore'] = query.published_before.isoformat()

            # Execute search
            search_response = self.youtube.search().list(**search_params).execute()

            # Extract video IDs for detailed information
            video_ids = [item['id']['videoId']
                         for item in search_response['items']]

            # Get detailed video information
            videos = self._get_video_details(video_ids)

            # Create search result
            result = SearchResult(
                query=query,
                videos=videos,
                total_results=search_response.get(
                    'pageInfo', {}).get('totalResults', 0)
            )

            logger.info(f"Found {len(videos)} videos for query: {query.query}")
            return result

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in video search: {e}")
            raise

    def _get_video_details(self, video_ids: List[str]) -> List[VideoData]:
        """Get detailed information for specific video IDs"""
        if not video_ids:
            return []

        try:
            # YouTube API allows max 50 IDs per request
            videos = []
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                batch_videos = self._fetch_video_batch(batch_ids)
                videos.extend(batch_videos)

            return videos

        except Exception as e:
            logger.error(f"Error getting video details: {e}")
            return []

    def _fetch_video_batch(self, video_ids: List[str]) -> List[VideoData]:
        """Fetch a batch of video details"""
        try:
            video_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()

            videos = []
            for item in video_response['items']:
                video = self._parse_video_item(item)
                if video:
                    videos.append(video)

            return videos

        except Exception as e:
            logger.error(f"Error fetching video batch: {e}")
            return []

    def _parse_video_item(self, item: Dict[str, Any]) -> Optional[VideoData]:
        """Parse YouTube API video item into VideoData model"""
        try:
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})

            # Parse duration
            duration_str = content_details.get('duration', 'PT0S')
            duration_seconds = int(isodate.parse_duration(
                duration_str).total_seconds())

            # Create video stats
            stats = VideoStats(
                view_count=int(statistics.get('viewCount', 0)),
                like_count=int(statistics.get('likeCount', 0)),
                comment_count=int(statistics.get('commentCount', 0)),
                duration_seconds=duration_seconds
            )

            # Determine category
            category = self._categorize_video(snippet.get(
                'title', ''), snippet.get('description', ''))

            # Parse published date
            published_at = datetime.fromisoformat(
                snippet['publishedAt'].replace('Z', '+00:00'))

            # Create video data
            video = VideoData(
                video_id=item['id'],
                title=snippet['title'],
                description=snippet.get('description', ''),
                channel_id=snippet['channelId'],
                channel_title=snippet['channelTitle'],
                published_at=published_at,
                duration=duration_str,
                category=category,
                stats=stats,
                tags=snippet.get('tags', []),
                thumbnail_url=snippet.get(
                    'thumbnails', {}).get('high', {}).get('url')
            )

            return video

        except Exception as e:
            logger.error(f"Error parsing video item: {e}")
            return None

    def _categorize_video(self, title: str, description: str) -> VideoCategory:
        """Categorize video based on title and description"""
        content = (title + ' ' + description).lower()

        # Simple keyword-based categorization
        if any(word in content for word in ['tutorial', 'learn', 'education', 'course']):
            return VideoCategory.EDUCATION
        elif any(word in content for word in ['tech', 'programming', 'software', 'ai']):
            return VideoCategory.TECHNOLOGY
        elif any(word in content for word in ['game', 'gaming', 'play']):
            return VideoCategory.GAMING
        elif any(word in content for word in ['music', 'song', 'album']):
            return VideoCategory.MUSIC
        elif any(word in content for word in ['news', 'breaking', 'report']):
            return VideoCategory.NEWS
        elif any(word in content for word in ['sport', 'football', 'basketball']):
            return VideoCategory.SPORTS
        else:
            return VideoCategory.OTHER

    def get_channel_info(self, channel_id: str) -> Optional[ChannelData]:
        """Get detailed channel information"""
        try:
            channel_response = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            ).execute()

            if not channel_response['items']:
                return None

            item = channel_response['items'][0]
            snippet = item['snippet']
            statistics = item.get('statistics', {})

            # Parse creation date
            created_at = None
            if 'publishedAt' in snippet:
                created_at = datetime.fromisoformat(
                    snippet['publishedAt'].replace('Z', '+00:00'))

            channel = ChannelData(
                channel_id=channel_id,
                title=snippet['title'],
                description=snippet.get('description', ''),
                subscriber_count=int(statistics.get('subscriberCount', 0)),
                video_count=int(statistics.get('videoCount', 0)),
                view_count=int(statistics.get('viewCount', 0)),
                created_at=created_at,
                thumbnail_url=snippet.get(
                    'thumbnails', {}).get('high', {}).get('url')
            )

            return channel

        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None

    def get_trending_videos(self, region_code: str = 'US', max_results: int = 25) -> List[VideoData]:
        """Get trending videos for a specific region"""
        try:
            videos_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                chart='mostPopular',
                regionCode=region_code,
                maxResults=min(max_results, 50)
            ).execute()

            videos = []
            for item in videos_response['items']:
                video = self._parse_video_item(item)
                if video:
                    videos.append(video)

            return videos

        except Exception as e:
            logger.error(f"Error getting trending videos: {e}")
            return []


# Example usage and testing
if __name__ == "__main__":
    # Test YouTube service
    try:
        # Initialize service
        youtube_service = YouTubeService()

        # Test search
        query = SearchQuery(
            query="python tutorial",
            max_results=5,
            order="viewCount"
        )

        results = youtube_service.search_videos(query)
        print(f"Search Results: {len(results.videos)} videos found")

        for video in results.videos:
            print(f"- {video.title} ({video.stats.view_count:,} views)") 

        print("\nYouTube service test completed successfully!")

    except Exception as e:
        print(f"YouTube service test failed: {e}")
        print("Please check your YouTube API key in the .env file")

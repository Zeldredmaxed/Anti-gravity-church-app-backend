"""YouTube Live Detection Service.

Allows churches to automatically detect when they go live on Sundays.
A manual toggle is available for mid-week services via the Sermons API.
"""

import urllib.request
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.models.sermon import Sermon
from app.models.church import Church
from app.config import settings

logger = logging.getLogger(__name__)


def check_youtube_live_status(db: Session):
    """
    Check all churches with a configured youtube_channel_id.
    Only auto-check on Sundays.
    """
    if not settings.YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY not set. Skipping live detection.")
        return

    now = datetime.now(timezone.utc)
    # Only run auto-detection on Sundays (weekday() == 6)
    if now.weekday() != 6:
        return

    churches = db.query(Church).filter(Church.youtube_channel_id.isnot(None)).all()
    
    for church in churches:
        try:
            _check_church_live(db, church)
        except Exception as e:
            logger.error(f"Failed to check YouTube live for church {church.id}: {e}")


def _check_church_live(db: Session, church: Church):
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&channelId={church.youtube_channel_id}"
        f"&type=video&eventType=live&key={settings.YOUTUBE_API_KEY}"
    )
    
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
    items = data.get("items", [])
    
    if items:
        # Currently live
        video_id = items[0]["id"]["videoId"]
        snippet = items[0]["snippet"]
        
        # Check if we already have an active live sermon for this video
        existing = db.query(Sermon).filter(
            Sermon.church_id == church.id,
            Sermon.youtube_video_id == video_id,
            Sermon.is_live == True
        ).first()
        
        if not existing:
            # Create a new live sermon entry
            new_sermon = Sermon(
                church_id=church.id,
                uploaded_by=church.pastor_id,  # default to pastor
                title=snippet.get("title", "Sunday Live Service"),
                description=snippet.get("description", ""),
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                video_type="youtube",
                youtube_video_id=video_id,
                thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
                is_live=True,
                live_started_at=datetime.now(timezone.utc),
                is_published=True
            )
            db.add(new_sermon)
            db.commit()
            logger.info(f"Church {church.id} went live: {video_id}")
            
    else:
        # Not currently live on YouTube.
        # Check if we have any active live sermons that should be closed.
        active_lives = db.query(Sermon).filter(
            Sermon.church_id == church.id,
            Sermon.is_live == True,
            Sermon.video_type == "youtube"
        ).all()
        
        for sermon in active_lives:
            sermon.is_live = False
            sermon.recorded_date = datetime.now(timezone.utc).date()
            logger.info(f"Church {church.id} live stream ended: {sermon.youtube_video_id}")
            
        if active_lives:
            db.commit()

from pydantic import BaseModel
from datetime import datetime, timezone

class WatchedVideo(BaseModel):
    video_id: str
    title: str
    url: str
    thumbnail_url: str
    watched_at: datetime = datetime.now(timezone.utc)
from pydantic import BaseModel, HttpUrl
from typing import List

class Video(BaseModel):
    id: str
    title: str
    created_at: str
    url : HttpUrl
    thumbnail_url: str

class VideoList(BaseModel):
    data: List[Video]

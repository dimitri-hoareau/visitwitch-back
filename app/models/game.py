from pydantic import BaseModel
from typing import List

class Game(BaseModel):
    id: str
    name: str
    box_art_url: str

class GameList(BaseModel):
    data: List[Game]
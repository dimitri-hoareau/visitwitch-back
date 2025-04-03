from pydantic import BaseModel
from typing import List

class Game(BaseModel):
    id: str
    name: str

class GameList(BaseModel):
    data: List[Game]
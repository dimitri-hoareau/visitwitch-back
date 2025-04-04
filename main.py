import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from app.models.game import Game, GameList
from app.models.video import  Video, VideoList

load_dotenv()


MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    app.mongodb = app.mongodb_client[DB_NAME]
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_twitch_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": TWITCH_CLIENT_ID,
                "client_secret": TWITCH_CLIENT_SECRET,
                "grant_type": "client_credentials"
            }
        )
        
        data = response.json()
        return data["access_token"]
    

@app.get("/twitch-games/{game_name}")
async def search_twitch_games(game_name:str):
    token = await get_twitch_token()

    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitch.tv/helix/search/categories",
            params={"query": game_name},
            headers={
                "Client-ID": TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {token}"
            },
        )

        print("*******************************************")
        print(response)
        twitch_data = response.json()
        
        games = []
        for item in twitch_data["data"]:
            games.append(Game(
                id=item["id"],
                name=item["name"]
            ))
        
        return GameList(data=games)

@app.get("/twitch-videos/{game_id}")
async def get_twitch_videos(game_id:str):
    token = await get_twitch_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitch.tv/helix/videos",
            params={"game_id": game_id}, 
            headers={
                "Client-ID": TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {token}"
            },
        )
        
        twitch_data = response.json()
        
        videos = []
        for item in twitch_data["data"]:
            videos.append(Video(
                id=item["id"],
                title=item["title"],
                created_at=item["created_at"],
                url=item["url"],
                thumbnail_url=item["thumbnail_url"]
            ))
        
        return VideoList(data=videos)
    

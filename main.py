import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from app.models.game import Game, GameList
from app.models.video import  Video, VideoList
from app.models.watched_videos import WatchedVideo
from datetime import datetime, timezone


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
async def search_twitch_games(game_name: str, max_results: bool = False):
    token = await get_twitch_token()
    
    games = []
    cursor = None
    
    async with httpx.AsyncClient() as client:
        while True:
            params = {
                "query": game_name,
                "first": 100 
            }
            
            if cursor:
                params["after"] = cursor
                
            response = await client.get(
                "https://api.twitch.tv/helix/search/categories",
                params=params,
                headers={
                    "Client-ID": TWITCH_CLIENT_ID,
                    "Authorization": f"Bearer {token}"
                }
            )
            
            twitch_data = response.json()
            
            for item in twitch_data["data"]:
                games.append(Game(
                    id=item["id"],
                    name=item["name"],
                    box_art_url=item.get("box_art_url")
                ))
            
            if (max_results and 
                "pagination" in twitch_data and 
                "cursor" in twitch_data["pagination"] and 
                len(twitch_data["data"]) > 0):
                cursor = twitch_data["pagination"]["cursor"]
            else:
                break
    
    return GameList(data=games)

@app.get("/twitch-videos/{game_id}")
async def get_twitch_videos(game_id: str, max_results: bool = False):
    token = await get_twitch_token()
    
    videos = []
    cursor = None
    
    async with httpx.AsyncClient() as client:
        while True:
            params = {
                "game_id": game_id,
                "first": 100 
            }
            
            if cursor:
                params["after"] = cursor
                
            response = await client.get(
                "https://api.twitch.tv/helix/videos",
                params=params,
                headers={
                    "Client-ID": TWITCH_CLIENT_ID,
                    "Authorization": f"Bearer {token}"
                }
            )
            
            twitch_data = response.json()
        
            for item in twitch_data["data"]:
                thumbnail_url = item["thumbnail_url"]
                thumbnail_url = thumbnail_url.replace("%{width}", "320").replace("%{height}", "180")
                
                videos.append(Video(
                    id=item["id"],
                    title=item["title"],
                    created_at=item["created_at"],
                    url=item["url"],
                    thumbnail_url=thumbnail_url
                ))
            
            if (max_results and 
                "pagination" in twitch_data and 
                "cursor" in twitch_data["pagination"] and 
                len(twitch_data["data"]) > 0):
                cursor = twitch_data["pagination"]["cursor"]
            else:
                break
    
    return VideoList(data=videos)


@app.post("/watched-videos", status_code=201)
async def add_watched_video(video: WatchedVideo):
    try:
        video_data = video.model_dump()
        
        video_data["watched_at"] = datetime.now(timezone.utc)
        
        await app.mongodb["watched_videos"].insert_one(video_data)
        
        return {
            "status": "success",
            "message": "The video is corretly downloaded",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
    

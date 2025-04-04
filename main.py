import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from app.models.game import Game, GameList

load_dotenv()

# Récupérer les identifiants Twitch depuis les variables d'environnement
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

app = FastAPI()

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
    

@app.get("/")
async def root():
    return {"greeting": "Hello world"}


@app.get("/test-game")
async def test_game():
    game = Game(
        id="123456",
        name="Minecraft",
    )

    game_list = GameList(data=[game])
    return game_list
    

@app.get("/twitch-games")
async def get_twitch_games():
    token = await get_twitch_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitch.tv/helix/games/top",
            headers={
                "Client-ID": TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {token}"
            },
        )
        
        twitch_data = response.json()
        
        games = []
        for item in twitch_data["data"]:
            games.append(Game(
                id=item["id"],
                name=item["name"]
            ))
        
        return GameList(data=games)
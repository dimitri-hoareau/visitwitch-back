from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from app.models.game import Game, GameList

app = FastAPI()

MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "visitwitch_db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    app.mongodb = app.mongodb_client[DB_NAME]
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

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
    
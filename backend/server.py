"""FastAPI server exposing AI agent endpoints."""

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from ai_agents.agents import AgentConfig, ChatAgent, SearchAgent
from hyperliquid_service import HyperliquidService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent


class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class ChatRequest(BaseModel):
    message: str
    agent_type: str = "chat"
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    agent_type: str
    capabilities: List[str]
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResponse(BaseModel):
    success: bool
    query: str
    summary: str
    search_results: Optional[dict] = None
    sources_count: int
    error: Optional[str] = None


class HyperliquidCoin(BaseModel):
    coin: str
    avg_funding_rate: float
    avg_funding_rate_pct: float
    open_interest_usd: float
    daily_volume_usd: float
    mark_price: float
    current_funding_rate: float
    funding_data_points: int


class HyperliquidResponse(BaseModel):
    success: bool
    coins: List[HyperliquidCoin]
    last_updated: datetime
    next_update: datetime
    error: Optional[str] = None


def _ensure_db(request: Request):
    try:
        return request.app.state.db
    except AttributeError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=503, detail="Database not ready") from exc


def _get_agent_cache(request: Request) -> Dict[str, object]:
    if not hasattr(request.app.state, "agent_cache"):
        request.app.state.agent_cache = {}
    return request.app.state.agent_cache


async def _get_or_create_agent(request: Request, agent_type: str):
    cache = _get_agent_cache(request)
    if agent_type in cache:
        return cache[agent_type]

    config: AgentConfig = request.app.state.agent_config

    if agent_type == "search":
        cache[agent_type] = SearchAgent(config)
    elif agent_type == "chat":
        cache[agent_type] = ChatAgent(config)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent type '{agent_type}'")

    return cache[agent_type]


async def update_hyperliquid_data(db):
    """Background task to update Hyperliquid data."""
    try:
        logger.info("Starting Hyperliquid data update...")
        service = HyperliquidService()
        coins = await service.get_top_funding_rate_coins()

        now = datetime.now(timezone.utc)
        next_update = now + timedelta(hours=1)

        # Store in MongoDB
        await db.hyperliquid_top_coins.delete_many({})  # Clear old data
        await db.hyperliquid_top_coins.insert_one({
            "coins": coins,
            "last_updated": now,
            "next_update": next_update,
        })

        logger.info(f"Hyperliquid data updated successfully. {len(coins)} coins stored.")
    except Exception as exc:
        logger.exception("Error updating Hyperliquid data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(ROOT_DIR / ".env")

    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME")

    if not mongo_url or not db_name:
        missing = [name for name, value in {"MONGO_URL": mongo_url, "DB_NAME": db_name}.items() if not value]
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    client = AsyncIOMotorClient(mongo_url)

    # Initialize scheduler
    scheduler = AsyncIOScheduler()

    try:
        app.state.mongo_client = client
        app.state.db = client[db_name]
        app.state.agent_config = AgentConfig()
        app.state.agent_cache = {}
        logger.info("AI Agents API starting up")

        # Initialize Hyperliquid data on startup
        await update_hyperliquid_data(app.state.db)

        # Schedule hourly updates
        scheduler.add_job(
            update_hyperliquid_data,
            "interval",
            hours=1,
            args=[app.state.db],
            id="hyperliquid_update",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduled hourly Hyperliquid data updates")

        yield
    finally:
        scheduler.shutdown()
        client.close()
        logger.info("AI Agents API shutdown complete")


app = FastAPI(
    title="AI Agents API",
    description="Minimal AI Agents API with LangGraph and MCP support",
    lifespan=lifespan,
)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "Hello World"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate, request: Request):
    db = _ensure_db(request)
    status_obj = StatusCheck(**input.model_dump())
    await db.status_checks.insert_one(status_obj.model_dump())
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks(request: Request):
    db = _ensure_db(request)
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_request: ChatRequest, request: Request):
    try:
        agent = await _get_or_create_agent(request, chat_request.agent_type)
        response = await agent.execute(chat_request.message)

        return ChatResponse(
            success=response.success,
            response=response.content,
            agent_type=chat_request.agent_type,
            capabilities=agent.get_capabilities(),
            metadata=response.metadata,
            error=response.error,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in chat endpoint")
        return ChatResponse(
            success=False,
            response="",
            agent_type=chat_request.agent_type,
            capabilities=[],
            error=str(exc),
        )


@api_router.post("/search", response_model=SearchResponse)
async def search_and_summarize(search_request: SearchRequest, request: Request):
    try:
        search_agent = await _get_or_create_agent(request, "search")
        search_prompt = (
            f"Search for information about: {search_request.query}. "
            "Provide a comprehensive summary with key findings."
        )
        result = await search_agent.execute(search_prompt, use_tools=True)

        if result.success:
            metadata = result.metadata or {}
            return SearchResponse(
                success=True,
                query=search_request.query,
                summary=result.content,
                search_results=metadata,
                sources_count=int(metadata.get("tool_run_count", metadata.get("tools_used", 0)) or 0),
            )

        return SearchResponse(
            success=False,
            query=search_request.query,
            summary="",
            sources_count=0,
            error=result.error,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in search endpoint")
        return SearchResponse(
            success=False,
            query=search_request.query,
            summary="",
            sources_count=0,
            error=str(exc),
        )


@api_router.get("/agents/capabilities")
async def get_agent_capabilities(request: Request):
    try:
        search_agent = await _get_or_create_agent(request, "search")
        chat_agent = await _get_or_create_agent(request, "chat")

        return {
            "success": True,
            "capabilities": {
                "search_agent": search_agent.get_capabilities(),
                "chat_agent": chat_agent.get_capabilities(),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error getting capabilities")
        return {"success": False, "error": str(exc)}


@api_router.get("/hyperliquid/top-coins", response_model=HyperliquidResponse)
async def get_hyperliquid_top_coins(request: Request, force_refresh: bool = False):
    """
    Get top 10 coins with highest average funding rate from Hyperliquid.

    Query Parameters:
        force_refresh: If True, force refresh the data from API instead of using cache
    """
    db = _ensure_db(request)

    try:
        # Check if we need to refresh
        cached_data = await db.hyperliquid_top_coins.find_one()

        if force_refresh or not cached_data:
            logger.info("Force refresh or no cached data, fetching from API...")
            await update_hyperliquid_data(db)
            cached_data = await db.hyperliquid_top_coins.find_one()

        if not cached_data:
            raise HTTPException(status_code=503, detail="Failed to fetch Hyperliquid data")

        # Check if data is stale (older than 1 hour)
        last_updated = cached_data["last_updated"]
        if isinstance(last_updated, datetime) and last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        if (now - last_updated).total_seconds() > 3600:  # 1 hour
            logger.info("Data is stale, refreshing...")
            await update_hyperliquid_data(db)
            cached_data = await db.hyperliquid_top_coins.find_one()

        coins = [HyperliquidCoin(**coin) for coin in cached_data["coins"]]

        # Ensure timezone awareness for response
        last_updated_tz = cached_data["last_updated"]
        next_update_tz = cached_data["next_update"]
        if isinstance(last_updated_tz, datetime) and last_updated_tz.tzinfo is None:
            last_updated_tz = last_updated_tz.replace(tzinfo=timezone.utc)
        if isinstance(next_update_tz, datetime) and next_update_tz.tzinfo is None:
            next_update_tz = next_update_tz.replace(tzinfo=timezone.utc)

        return HyperliquidResponse(
            success=True,
            coins=coins,
            last_updated=last_updated_tz,
            next_update=next_update_tz,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error fetching Hyperliquid data")
        return HyperliquidResponse(
            success=False,
            coins=[],
            last_updated=datetime.now(timezone.utc),
            next_update=datetime.now(timezone.utc),
            error=str(exc),
        )


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

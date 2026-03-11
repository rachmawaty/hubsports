"""
HubSports - Official MCP (Model Context Protocol) Implementation
Following: https://modelcontextprotocol.io/
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
import httpx
from datetime import datetime, timezone, timedelta
from dateutil import parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HubSports MCP Server", version="1.0.0")

# ============================================================================
# MCP PROTOCOL MODELS (JSON-RPC 2.0)
# ============================================================================

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[str | int] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[str | int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MCPError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


# ============================================================================
# ESPN API INTEGRATION (same as before)
# ============================================================================

TEAMS = {
    "patriots": {
        "name": "New England Patriots",
        "sport": "NFL",
        "emoji": "🏈",
        "api": "http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/ne/schedule"
    },
    "celtics": {
        "name": "Boston Celtics",
        "sport": "NBA",
        "emoji": "🏀",
        "api": "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/bos/schedule"
    },
    "bruins": {
        "name": "Boston Bruins",
        "sport": "NHL",
        "emoji": "🏒",
        "api": "http://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/bos/schedule"
    },
    "redsox": {
        "name": "Boston Red Sox",
        "sport": "MLB",
        "emoji": "⚾",
        "api": "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/bos/schedule"
    }
}


async def fetch_team_schedule(team_key: str, days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Fetch upcoming games for a team from ESPN API"""
    team = TEAMS[team_key]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(team["api"])
            response.raise_for_status()
            data = response.json()
        
        games = []
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_ahead)
        
        events = data.get("events", [])
        
        for event in events:
            try:
                game_date_str = event.get("date")
                if not game_date_str:
                    continue
                
                game_date = parser.parse(game_date_str)
                
                if game_date < now or game_date > cutoff:
                    continue
                
                competitions = event.get("competitions", [])
                if not competitions:
                    continue
                
                comp = competitions[0]
                competitors = comp.get("competitors", [])
                
                home_team = None
                away_team = None
                
                for competitor in competitors:
                    team_info = competitor.get("team", {})
                    if competitor.get("homeAway") == "home":
                        home_team = team_info.get("displayName", "Unknown")
                    else:
                        away_team = team_info.get("displayName", "Unknown")
                
                venue = comp.get("venue", {}).get("fullName", "TBD")
                status = event.get("status", {}).get("type", {}).get("name", "Scheduled")
                
                game = {
                    "team": team["name"],
                    "sport": team["sport"],
                    "emoji": team["emoji"],
                    "date": game_date.isoformat(),
                    "date_str": game_date.strftime("%a, %b %d at %I:%M %p"),
                    "home": home_team,
                    "away": away_team,
                    "venue": venue,
                    "status": status
                }
                
                games.append(game)
                
            except Exception as e:
                logger.warning(f"Error parsing game for {team_key}: {e}")
                continue
        
        return games
        
    except Exception as e:
        logger.error(f"Failed to fetch schedule for {team_key}: {e}")
        return []


async def get_all_upcoming_games(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Get all upcoming games for all Boston teams"""
    all_games = []
    
    for team_key in TEAMS.keys():
        games = await fetch_team_schedule(team_key, days_ahead)
        all_games.extend(games)
    
    all_games.sort(key=lambda g: g["date"])
    
    return all_games


# ============================================================================
# MCP PROTOCOL HANDLERS
# ============================================================================

async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize request"""
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "hubsports-mcp",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {}
        }
    }


async def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tools/list request - return available tools"""
    return {
        "tools": [
            {
                "name": "get_boston_sports_schedule",
                "description": "Get upcoming game schedules for Boston sports teams (Patriots, Celtics, Bruins, Red Sox). Returns game dates, matchups, venues, and status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "team": {
                            "type": "string",
                            "enum": ["patriots", "celtics", "bruins", "redsox", "all"],
                            "description": "Which team to get schedule for, or 'all' for all teams",
                            "default": "all"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days ahead to search (1-30)",
                            "default": 14,
                            "minimum": 1,
                            "maximum": 30
                        }
                    }
                }
            }
        ]
    }


async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tools/call request - execute a tool"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name != "get_boston_sports_schedule":
        raise ValueError(f"Unknown tool: {tool_name}")
    
    # Extract parameters
    team = arguments.get("team", "all")
    days = arguments.get("days", 14)
    
    # Validate
    if days < 1 or days > 30:
        days = 14
    
    # Fetch games
    if team == "all":
        games = await get_all_upcoming_games(days)
    elif team in TEAMS:
        games = await fetch_team_schedule(team, days)
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: Unknown team '{team}'. Valid teams: patriots, celtics, bruins, redsox, all"
                }
            ],
            "isError": True
        }
    
    # Format response
    if not games:
        text = f"No upcoming games found for {team} in the next {days} days."
    else:
        lines = [f"🏒 Upcoming Boston Sports ({len(games)} games in next {days} days):\n"]
        for game in games[:10]:  # Limit to 10 for readability
            lines.append(
                f"{game['emoji']} {game['sport']}: "
                f"{game['away']} @ {game['home']}\n"
                f"   📅 {game['date_str']}\n"
                f"   📍 {game['venue']}\n"
            )
        text = "\n".join(lines)
    
    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "isError": False
    }


# ============================================================================
# MCP JSON-RPC ENDPOINT
# ============================================================================

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Official MCP endpoint using JSON-RPC 2.0
    
    This follows the Model Context Protocol specification from:
    https://modelcontextprotocol.io/
    """
    try:
        body = await request.json()
        rpc_request = JSONRPCRequest(**body)
        
        logger.info(f"MCP Request: {rpc_request.method}")
        
        # Route to appropriate handler
        if rpc_request.method == "initialize":
            result = await handle_initialize(rpc_request.params or {})
        
        elif rpc_request.method == "tools/list":
            result = await handle_tools_list(rpc_request.params or {})
        
        elif rpc_request.method == "tools/call":
            result = await handle_tools_call(rpc_request.params or {})
        
        else:
            return JSONRPCResponse(
                id=rpc_request.id,
                error=MCPError(
                    code=-32601,
                    message=f"Method not found: {rpc_request.method}"
                ).dict()
            ).dict()
        
        return JSONRPCResponse(
            id=rpc_request.id,
            result=result
        ).dict()
        
    except Exception as e:
        logger.error(f"MCP Error: {e}")
        return JSONRPCResponse(
            id=body.get("id") if isinstance(body, dict) else None,
            error=MCPError(
                code=-32603,
                message=str(e)
            ).dict()
        ).dict()


# ============================================================================
# INFO ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "HubSports MCP Server",
        "version": "1.0.0",
        "protocol": "Model Context Protocol (MCP)",
        "spec": "https://modelcontextprotocol.io/",
        "endpoints": {
            "/mcp": "Official MCP JSON-RPC 2.0 endpoint",
            "/docs": "OpenAPI/Swagger documentation"
        },
        "available_tools": [
            "get_boston_sports_schedule"
        ]
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "protocol": "MCP"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)

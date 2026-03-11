"""
HubSports - Boston Sports Schedule MCP Agent
Fetches upcoming games for Patriots, Celtics, Bruins, and Red Sox
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timedelta
from dateutil import parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HubSports MCP Agent", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Team configurations - ESPN API endpoints
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


class MCPDecideRequest(BaseModel):
    """MCP /decide request format"""
    agent_id: str
    state: Dict[str, Any]


class MCPAction(BaseModel):
    """MCP action format"""
    action: str
    target: Optional[str] = None
    amount: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


async def fetch_team_schedule(team_key: str, days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Fetch upcoming games for a team from ESPN API"""
    team = TEAMS[team_key]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(team["api"])
            response.raise_for_status()
            data = response.json()
        
        games = []
        from datetime import timezone
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_ahead)
        
        # Parse ESPN response
        events = data.get("events", [])
        
        for event in events:
            try:
                game_date_str = event.get("date")
                if not game_date_str:
                    continue
                
                game_date = parser.parse(game_date_str)
                
                # Only include upcoming games within the window
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
    
    # Sort by date
    all_games.sort(key=lambda g: g["date"])
    
    return all_games


# ============================================================================
# MCP PROTOCOL ENDPOINTS
# ============================================================================

@app.post("/decide")
async def mcp_decide(request: MCPDecideRequest) -> Dict[str, Any]:
    """
    MCP /decide endpoint - called by AgenticTown orchestrator each cycle
    
    Returns actions the agent wants to take based on current town state
    """
    logger.info(f"🏒 HubSports decision cycle {request.state.get('cycle', 0)}")
    
    # Fetch upcoming games
    games = await get_all_upcoming_games(days_ahead=7)
    
    # Build summary message
    if not games:
        message = "📅 No upcoming Boston sports games in the next 7 days"
    else:
        lines = [f"📅 Upcoming Boston Sports ({len(games)} games):"]
        for game in games[:5]:  # Show next 5 games
            lines.append(
                f"{game['emoji']} {game['sport']}: "
                f"{game['away']} @ {game['home']} - {game['date_str']}"
            )
        message = "\n".join(lines)
    
    # For now, this agent just reports data - doesn't take town actions
    # But we return the data in action metadata
    return {
        "agent_id": request.agent_id,
        "actions": [],  # Not contributing/voting, just providing info
        "message": message,
        "metadata": {
            "games_count": len(games),
            "games": games[:10],  # Include top 10 in metadata
            "last_updated": datetime.now().isoformat()
        }
    }


# ============================================================================
# STANDALONE ENDPOINTS (for direct querying)
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "HubSports",
        "version": "1.0.0",
        "description": "Boston sports schedule aggregator (Patriots, Celtics, Bruins, Red Sox)",
        "teams": list(TEAMS.keys()),
        "endpoints": {
            "/schedule": "Get all upcoming games",
            "/schedule/{team}": "Get games for specific team",
            "/decide": "MCP protocol endpoint for AgenticTown"
        }
    }


@app.get("/schedule")
async def get_schedule(days: int = 14):
    """Get all upcoming Boston sports games"""
    games = await get_all_upcoming_games(days_ahead=days)
    
    return {
        "success": True,
        "count": len(games),
        "games": games
    }


@app.get("/schedule/{team}")
async def get_team_schedule(team: str, days: int = 14):
    """Get upcoming games for specific team"""
    team = team.lower()
    
    if team not in TEAMS:
        return {
            "success": False,
            "error": f"Unknown team: {team}",
            "available": list(TEAMS.keys())
        }
    
    games = await fetch_team_schedule(team, days_ahead=days)
    
    return {
        "success": True,
        "team": TEAMS[team]["name"],
        "sport": TEAMS[team]["sport"],
        "count": len(games),
        "games": games
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "app": "HubSports"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

"""
HubSports - MCP Server (Official SDK, Streamable HTTP Transport)
Spec: https://modelcontextprotocol.io/
SDK:  https://github.com/modelcontextprotocol/python-sdk
"""

import httpx
import logging
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MCP SERVER
# ============================================================================

mcp = FastMCP(
    "HubSports",
    instructions="Provides upcoming game schedules for Boston sports teams: Patriots (NFL), Celtics (NBA), Bruins (NHL), and Red Sox (MLB). Data is sourced live from ESPN.",
    stateless_http=True,
)

# ============================================================================
# ESPN API INTEGRATION
# ============================================================================

TEAMS = {
    "patriots": {
        "name": "New England Patriots",
        "sport": "NFL",
        "emoji": "🏈",
        "api": "http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/ne/schedule",
    },
    "celtics": {
        "name": "Boston Celtics",
        "sport": "NBA",
        "emoji": "🏀",
        "api": "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/bos/schedule",
    },
    "bruins": {
        "name": "Boston Bruins",
        "sport": "NHL",
        "emoji": "🏒",
        "api": "http://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/bos/schedule",
    },
    "redsox": {
        "name": "Boston Red Sox",
        "sport": "MLB",
        "emoji": "⚾",
        "api": "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/bos/schedule",
    },
}


async def fetch_team_schedule(team_key: str, days_ahead: int = 14) -> list[dict]:
    team = TEAMS[team_key]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(team["api"])
            response.raise_for_status()
            data = response.json()

        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_ahead)
        games = []

        for event in data.get("events", []):
            try:
                game_date_str = event.get("date")
                if not game_date_str:
                    continue
                game_date = dateparser.parse(game_date_str)
                if game_date < now or game_date > cutoff:
                    continue

                comp = (event.get("competitions") or [{}])[0]
                home_team, away_team = None, None
                for competitor in comp.get("competitors", []):
                    name = competitor.get("team", {}).get("displayName", "Unknown")
                    if competitor.get("homeAway") == "home":
                        home_team = name
                    else:
                        away_team = name

                games.append({
                    "team": team["name"],
                    "sport": team["sport"],
                    "emoji": team["emoji"],
                    "date": game_date.isoformat(),
                    "date_str": game_date.strftime("%a, %b %d at %I:%M %p UTC"),
                    "home": home_team or "TBD",
                    "away": away_team or "TBD",
                    "venue": comp.get("venue", {}).get("fullName", "TBD"),
                    "status": event.get("status", {}).get("type", {}).get("name", "Scheduled"),
                })
            except Exception as e:
                logger.warning(f"Error parsing game for {team_key}: {e}")
        return games

    except Exception as e:
        logger.error(f"Failed to fetch schedule for {team_key}: {e}")
        return []


# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool()
async def get_boston_sports_schedule(team: str = "all", days: int = 14) -> str:
    """
    Get upcoming game schedules for Boston sports teams.

    Args:
        team: Team to query — "patriots", "celtics", "bruins", "redsox", or "all" (default: "all")
        days: Number of days ahead to look (1–30, default: 14)
    """
    days = max(1, min(30, days))

    if team == "all":
        all_games = []
        for key in TEAMS:
            all_games.extend(await fetch_team_schedule(key, days))
        all_games.sort(key=lambda g: g["date"])
    elif team in TEAMS:
        all_games = await fetch_team_schedule(team, days)
    else:
        return f"Unknown team '{team}'. Valid options: {', '.join(TEAMS.keys())}, all"

    if not all_games:
        label = TEAMS[team]["name"] if team != "all" else "any Boston team"
        return f"No upcoming games found for {label} in the next {days} days."

    label = TEAMS[team]["name"] if team != "all" else "All Boston Teams"
    lines = [f"📅 {label} — Next {days} Days ({len(all_games)} games)\n"]
    for g in all_games:
        lines.append(
            f"{g['emoji']} {g['sport']}: {g['away']} @ {g['home']}\n"
            f"   📅 {g['date_str']}\n"
            f"   📍 {g['venue']}  |  {g['status']}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def list_supported_teams() -> str:
    """List all Boston sports teams supported by HubSports."""
    lines = ["🏙️ HubSports — Supported Teams\n"]
    for key, info in TEAMS.items():
        lines.append(f"{info['emoji']} {info['name']} ({info['sport']})  →  key: \"{key}\"")
    return "\n".join(lines)


# ============================================================================
# ENTRYPOINT — expose ASGI app for uvicorn (Streamable HTTP at /mcp)
# ============================================================================

app = mcp.streamable_http_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)

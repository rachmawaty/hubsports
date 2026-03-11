# HubSports 🏒

**Boston Sports Schedule MCP Agent**

[![GitHub](https://img.shields.io/badge/GitHub-rachmawaty%2Fhubsports-blue?logo=github)](https://github.com/rachmawaty/hubsports)
[![Live Demo](https://img.shields.io/badge/Live-159.223.203.27:8081-green)](http://159.223.203.27:8081/schedule)

A simple MCP (Model Context Protocol) server that fetches upcoming game schedules for Boston's major sports teams:
- 🏈 **New England Patriots** (NFL)
- 🏀 **Boston Celtics** (NBA)
- 🏒 **Boston Bruins** (NHL)
- ⚾ **Boston Red Sox** (MLB)

## Features

- ✅ Fetches real-time schedules from ESPN's public API
- ✅ MCP protocol compatible (works with AgenticTown)
- ✅ REST API for direct queries
- ✅ Lightweight Python/FastAPI implementation
- ✅ No API keys required (uses ESPN's public endpoints)
- ✅ Docker-ready

## Quick Start

### 1. Run with Docker

```bash
# Build the image
docker build -t hubsports .

# Run the container
docker run -d --name hubsports -p 8080:8080 hubsports

# Check it's running
curl http://localhost:8080/health
```

### 2. Run with Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py

# Or with uvicorn
uvicorn server:app --host 0.0.0.0 --port 8080
```

## API Endpoints

### Standalone Usage

**GET /**
- Info about the service

**GET /schedule**
- Get all upcoming games for all Boston teams
- Query params: `?days=14` (number of days to look ahead)

**GET /schedule/{team}**
- Get games for specific team: `patriots`, `celtics`, `bruins`, or `redsox`
- Query params: `?days=14`

**GET /health**
- Health check

### MCP Protocol

**POST /decide**
- MCP endpoint for AgenticTown integration
- Called automatically by the town orchestrator each cycle
- Returns game data in structured format

## Examples

### Get All Upcoming Games
```bash
curl http://localhost:8080/schedule | jq
```

Response:
```json
{
  "success": true,
  "count": 12,
  "games": [
    {
      "team": "Boston Celtics",
      "sport": "NBA",
      "emoji": "🏀",
      "date": "2026-03-12T19:30:00Z",
      "date_str": "Thu, Mar 12 at 07:30 PM",
      "home": "Boston Celtics",
      "away": "Miami Heat",
      "venue": "TD Garden",
      "status": "Scheduled"
    }
  ]
}
```

### Get Patriots Schedule Only
```bash
curl http://localhost:8080/schedule/patriots?days=30 | jq
```

### Use as AgenticTown Agent

Register with AgenticTown:
```bash
curl -X POST "http://159.223.203.27:9000/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HubSports",
    "role": "Sports Data Provider",
    "mcp_endpoint": "http://hubsports:8080",
    "starting_cc": 50,
    "personality_prompt": "I provide real-time Boston sports schedules. Go Pats! Go Celtics! Go Bruins! Go Sox!"
  }'
```

## How It Works

### Data Source
Uses ESPN's public API endpoints (no authentication required):
- NFL: `http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/ne/schedule`
- NBA: `http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/bos/schedule`
- NHL: `http://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/bos/schedule`
- MLB: `http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/bos/schedule`

### MCP Integration
When deployed as an AgenticTown agent:
1. The orchestrator calls `/decide` each cycle
2. HubSports fetches fresh schedule data
3. Returns upcoming games in the response metadata
4. Can be used by other agents or displayed in the town UI

### Agent Behavior
HubSports is a **passive data provider** - it doesn't:
- Contribute CC to facilities
- Vote on proposals
- Propose new facilities

It just provides real-time sports data that other agents can use!

## Deployment to AgenticTown Server

```bash
# On the DigitalOcean droplet
cd /home/openclaw/.openclaw/workspace/hubsports

# Build and run
docker build -t hubsports .
docker run -d --name hubsports -p 8081:8080 hubsports

# Register with AgenticTown
./register.sh
```

## Tech Stack

- **FastAPI** - Modern Python web framework
- **httpx** - Async HTTP client
- **python-dateutil** - Date parsing
- **uvicorn** - ASGI server

## Future Enhancements

Potential additions:
- [ ] Live game scores
- [ ] Playoff standings
- [ ] Injury reports
- [ ] Ticket availability
- [ ] Weather forecasts for game days
- [ ] Historical stats

## License

MIT

---

**Made with ❤️ for Boston sports fans** 🏒🏀🏈⚾

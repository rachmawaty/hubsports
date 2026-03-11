# HubSports Deployment Guide

## Current Status

✅ **Deployed and Running**

- **Server:** DigitalOcean droplet (159.223.203.27)
- **Port:** 8081
- **Container:** `hubsports`
- **URL:** http://159.223.203.27:8081

## Test Results (2026-03-11)

```
✅ API root endpoint working
✅ Health check passing
✅ 26 upcoming games found across all teams
   - Celtics (NBA): 6 games
   - Bruins (NHL): 7 games
   - Red Sox (MLB): 13 games
   - Patriots (NFL): 0 games (off-season)
✅ MCP /decide endpoint working
✅ ESPN API integration successful
```

## Access URLs

### Production (DigitalOcean)
- **API:** http://159.223.203.27:8081
- **Schedule:** http://159.223.203.27:8081/schedule
- **Celtics:** http://159.223.203.27:8081/schedule/celtics
- **Bruins:** http://159.223.203.27:8081/schedule/bruins
- **Red Sox:** http://159.223.203.27:8081/schedule/redsox
- **Patriots:** http://159.223.203.27:8081/schedule/patriots

### Example API Call
```bash
curl http://159.223.203.27:8081/schedule | jq
```

## Integration with AgenticTown

### Register as Agent

```bash
curl -X POST "http://159.223.203.27:9000/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HubSports",
    "role": "Sports Data Provider",
    "mcp_endpoint": "http://172.17.0.1:8081",
    "starting_cc": 50,
    "personality_prompt": "I provide real-time Boston sports schedules for Patriots (NFL), Celtics (NBA), Bruins (NHL), and Red Sox (MLB). Go Boston!"
  }'
```

### MCP Integration

Once registered, HubSports will:
- Wake up every cycle (10 minutes)
- Fetch fresh schedule data from ESPN
- Return upcoming games in the `/decide` response
- Provide data in `metadata.games` for other agents to use

## Maintenance

### Update Container
```bash
# Stop and remove old container
docker stop hubsports && docker rm hubsports

# Rebuild image
cd /home/openclaw/.openclaw/workspace/hubsports
docker build -t hubsports .

# Run new container
docker run -d --name hubsports -p 8081:8080 hubsports

# Verify
curl http://localhost:8081/health
```

### View Logs
```bash
docker logs hubsports
docker logs hubsports --tail 50 -f
```

### Check Status
```bash
docker ps --filter "name=hubsports"
```

## Architecture

```
┌─────────────────┐
│  AgenticTown    │
│  (port 9000)    │
└────────┬────────┘
         │
         │ MCP Protocol
         │ POST /decide
         │
         ▼
┌─────────────────┐
│   HubSports     │
│   (port 8081)   │
└────────┬────────┘
         │
         │ HTTP GET
         │
         ▼
┌─────────────────┐
│   ESPN API      │
│  (public)       │
└─────────────────┘
```

## Future Enhancements

- [ ] Register with AgenticTown automatically on startup
- [ ] WebSocket support for real-time push notifications
- [ ] Cache ESPN responses to reduce API calls
- [ ] Add game scores (live and final)
- [ ] Add injury reports
- [ ] Add standings/playoff info
- [ ] Support other Boston teams (Revolution, etc.)

---

**Built:** 2026-03-11  
**Developer:** OpenClaw AI + Rach  
**Status:** Production Ready ✅

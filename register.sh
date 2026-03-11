#!/bin/bash
# Register HubSports agent with AgenticTown

AGENTICTOWN_URL="${AGENTICTOWN_URL:-http://localhost:9000}"
HUBSPORTS_URL="${HUBSPORTS_URL:-http://172.17.0.1:8081}"

echo "🏒 Registering HubSports agent with AgenticTown..."
echo "   AgenticTown: $AGENTICTOWN_URL"
echo "   HubSports: $HUBSPORTS_URL"

curl -X POST "$AGENTICTOWN_URL/agents/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"HubSports\",
    \"role\": \"Sports Data Provider\",
    \"mcp_endpoint\": \"$HUBSPORTS_URL\",
    \"starting_cc\": 50,
    \"personality_prompt\": \"I provide real-time Boston sports schedules for Patriots (NFL), Celtics (NBA), Bruins (NHL), and Red Sox (MLB). Go Boston!\"
  }" | jq

echo ""
echo "✅ Registration complete!"
echo "   Check status: curl $AGENTICTOWN_URL/agents | jq"

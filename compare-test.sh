#!/bin/bash
# Compare REST API vs Official MCP implementations

echo "🏒 HubSports Implementation Comparison"
echo "======================================"
echo ""

# REST API Test
echo "1️⃣  REST API (Custom) - https://hubsports.rach.es"
echo "------------------------------------------------"
echo ""
echo "Request: GET /schedule/celtics?days=7"
echo ""
curl -s "http://localhost:8081/schedule/celtics?days=7" | jq '{
  implementation: "REST API",
  count: .count,
  first_game: .games[0].date_str,
  protocol: "HTTP GET"
}'
echo ""
echo ""

# Official MCP Test
echo "2️⃣  Official MCP (JSON-RPC 2.0) - https://mcp.rach.es"
echo "---------------------------------------------------"
echo ""
echo "Request: JSON-RPC tools/call"
echo ""
curl -s -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_boston_sports_schedule",
      "arguments": {
        "team": "celtics",
        "days": 7
      }
    }
  }' | jq '{
  implementation: "Official MCP",
  protocol: .jsonrpc,
  id: .id,
  has_result: (.result != null),
  has_error: (.error != null),
  content_preview: .result.content[0].text[:100] + "..."
}'
echo ""
echo ""

echo "📊 Summary"
echo "=========="
echo ""
echo "REST API:"
echo "  ✅ Simple HTTP GET request"
echo "  ✅ Direct JSON response"
echo "  ✅ Easy to curl/test"
echo "  ❌ No standard protocol"
echo "  ❌ No discovery mechanism"
echo ""
echo "Official MCP:"
echo "  ✅ Standard JSON-RPC 2.0 protocol"
echo "  ✅ Built-in tool discovery (tools/list)"
echo "  ✅ Schema validation"
echo "  ✅ Compatible with MCP ecosystem"
echo "  ❌ More complex requests"
echo ""
echo "Both return the same underlying data from ESPN! 🏀"

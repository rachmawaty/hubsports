#!/bin/bash
# Quick test script for HubSports

BASE_URL="${BASE_URL:-http://localhost:8081}"

echo "🏒 Testing HubSports API..."
echo ""

echo "1️⃣  Testing root endpoint..."
curl -s "$BASE_URL/" | jq -r '.app, .version'
echo ""

echo "2️⃣  Testing health check..."
curl -s "$BASE_URL/health" | jq -r '.status'
echo ""

echo "3️⃣  Fetching all upcoming games..."
curl -s "$BASE_URL/schedule" | jq -r '"\(.count) upcoming games found"'
echo ""

echo "4️⃣  Celtics schedule..."
curl -s "$BASE_URL/schedule/celtics" | jq -r '"\(.count) Celtics games"'
echo ""

echo "5️⃣  Patriots schedule..."
curl -s "$BASE_URL/schedule/patriots" | jq -r '"\(.count) Patriots games"'
echo ""

echo "6️⃣  Bruins schedule..."
curl -s "$BASE_URL/schedule/bruins" | jq -r '"\(.count) Bruins games"'
echo ""

echo "7️⃣  Red Sox schedule..."
curl -s "$BASE_URL/schedule/redsox" | jq -r '"\(.count) Red Sox games"'
echo ""

echo "8️⃣  Testing MCP /decide endpoint..."
curl -s -X POST "$BASE_URL/decide" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "test", "state": {"cycle": 1}}' | jq -r '.message'
echo ""

echo "✅ All tests complete!"

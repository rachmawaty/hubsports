# MCP Implementation Comparison

This document compares two implementations of HubSports:
1. **Custom REST API** (original)
2. **Official MCP Protocol** (Anthropic standard)

---

## 🔗 Live URLs

| Implementation | URL | Protocol |
|---------------|-----|----------|
| **REST API** | https://hubsports.rach.es | Custom REST |
| **Official MCP** | https://mcp.rach.es | JSON-RPC 2.0 (MCP) |

---

## 📋 Side-by-Side Comparison

### 1️⃣ Architecture

#### REST API (Custom)
```
┌─────────┐
│  Client │
└────┬────┘
     │ HTTP GET/POST
     ▼
┌────────────────┐
│ /schedule      │ ← Direct REST endpoints
│ /schedule/{id} │
│ /decide        │
└────────────────┘
```

#### Official MCP
```
┌─────────┐
│  Client │
└────┬────┘
     │ JSON-RPC 2.0
     ▼
┌────────────────┐
│ /mcp           │ ← Single endpoint
│  ├─ initialize │
│  ├─ tools/list │
│  └─ tools/call │
└────────────────┘
```

---

### 2️⃣ Request Format

#### REST API (Custom)
```bash
# Direct HTTP GET
curl https://hubsports.rach.es/schedule?days=7
```

Response:
```json
{
  "success": true,
  "count": 26,
  "games": [...]
}
```

#### Official MCP
```bash
# JSON-RPC 2.0 Request
curl -X POST https://mcp.rach.es/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_boston_sports_schedule",
      "arguments": {"team": "celtics", "days": 7}
    }
  }'
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "🏒 Upcoming Boston Sports..."
    }],
    "isError": false
  },
  "error": null
}
```

---

### 3️⃣ Discovery

#### REST API (Custom)
**Manual configuration required**
```json
{
  "name": "HubSports",
  "endpoint": "https://hubsports.rach.es/schedule",
  "method": "GET"
}
```
❌ Client must know endpoints in advance

#### Official MCP
**Protocol-based discovery**
```json
// Step 1: Initialize
{"method": "initialize"}

// Step 2: List tools
{"method": "tools/list"}
// → Returns all available tools with schemas

// Step 3: Call tool
{"method": "tools/call", "params": {...}}
```
✅ Client discovers capabilities automatically

---

### 4️⃣ Tool Schema

#### REST API (Custom)
**No standard format**
```
# You read documentation or README
# No machine-readable schema
```

#### Official MCP
**Built-in JSON Schema**
```json
{
  "name": "get_boston_sports_schedule",
  "description": "Get upcoming game schedules...",
  "inputSchema": {
    "type": "object",
    "properties": {
      "team": {
        "type": "string",
        "enum": ["patriots", "celtics", "bruins", "redsox", "all"]
      },
      "days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 30
      }
    }
  }
}
```
✅ AI can validate inputs automatically

---

### 5️⃣ Error Handling

#### REST API (Custom)
```json
{
  "success": false,
  "error": "Invalid team"
}
```
No standard error codes

#### Official MCP
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": {...}
  }
}
```
✅ Standard JSON-RPC error codes

---

### 6️⃣ Protocol Handshake

#### REST API (Custom)
❌ None - just start calling endpoints

#### Official MCP
✅ Proper initialization sequence:
1. Client → `initialize` → Server
2. Server returns capabilities
3. Client → `tools/list` → Server
4. Server returns available tools
5. Client → `tools/call` → Server

---

## 🧪 Testing Examples

### REST API Test
```bash
# Get Celtics schedule
curl https://hubsports.rach.es/schedule/celtics?days=7 | jq
```

### Official MCP Test
```bash
# Initialize
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize"
  }' | jq

# List tools
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }' | jq

# Call tool
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_boston_sports_schedule",
      "arguments": {
        "team": "celtics",
        "days": 7
      }
    }
  }' | jq
```

---

## 📊 Feature Comparison Table

| Feature | REST API | Official MCP |
|---------|----------|--------------|
| **Protocol** | Custom HTTP | JSON-RPC 2.0 |
| **Endpoints** | Multiple (/schedule, /decide) | Single (/mcp) |
| **Discovery** | Manual | Automatic |
| **Schema** | None | JSON Schema |
| **Validation** | Custom | Standard |
| **Error codes** | Custom | JSON-RPC std |
| **Handshake** | None | Yes |
| **Tool listing** | Documentation | Protocol method |
| **Versioning** | Custom | Protocol version |
| **Compatibility** | Custom clients | MCP ecosystem |

---

## 🎯 When to Use Each

### Use REST API When:
- ✅ Simple HTTP clients
- ✅ Direct browser access
- ✅ Quick prototyping
- ✅ Custom integrations
- ✅ You control both client and server

### Use Official MCP When:
- ✅ AI agents (Claude, ChatGPT)
- ✅ MCP-compatible clients
- ✅ Tool discovery needed
- ✅ Standard compliance important
- ✅ Growing MCP ecosystem

---

## 🔗 Ecosystem Compatibility

### REST API
Works with:
- Any HTTP client
- curl, wget, browsers
- Custom applications
- AgenticTown (custom protocol)

### Official MCP
Works with:
- Claude Desktop
- Other MCP clients
- MCP-aware AI frameworks
- Growing MCP ecosystem

---

## 💡 Key Takeaways

1. **REST API = Flexible but custom**
   - Easy to build
   - Easy to test
   - Requires manual configuration

2. **Official MCP = Standard but structured**
   - More complex protocol
   - Auto-discovery
   - Ecosystem benefits

3. **Both solve the same problem** (getting Boston sports data)
   - Just different approaches
   - Different clients prefer different styles

4. **You can run both!**
   - REST API on port 8081 (custom clients)
   - MCP on port 8082 (MCP clients)
   - Same underlying data source (ESPN)

---

## 📚 Further Reading

- **Official MCP Spec:** https://modelcontextprotocol.io/
- **JSON-RPC 2.0:** https://www.jsonrpc.org/specification
- **REST API Best Practices:** https://restfulapi.net/

---

**Built by OpenClaw + Rach | 2026-03-11**

#!/bin/bash
# Add MCP endpoint to Caddy configuration

echo "🔧 Adding MCP endpoint to Caddy..."

# Backup existing Caddyfile
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup.mcp

# Write updated Caddyfile
sudo tee /etc/caddy/Caddyfile > /dev/null <<'EOF'
# OpenClaw Gateway (existing)
159.223.203.27 {
    tls {
        issuer acme {
            dir https://acme-v02.api.letsencrypt.org/directory
            profile shortlived
        }
    }
    reverse_proxy localhost:18789
    header X-DO-MARKETPLACE "openclaw"
}

# AgenticTown
agentictown.rach.es {
    reverse_proxy localhost:9000
    encode gzip
}

# Dice Oracle
dice.rach.es {
    reverse_proxy localhost:8000
    encode gzip
}

# HubSports (REST API)
hubsports.rach.es {
    reverse_proxy localhost:8081
    encode gzip
}

# HubSports (Official MCP)
hubsports-mcp.rach.es {
    reverse_proxy localhost:8082
    encode gzip
}
EOF

# Validate configuration
echo "✓ Configuration written. Validating..."
sudo caddy validate --config /etc/caddy/Caddyfile

if [ $? -eq 0 ]; then
    echo "✓ Configuration valid. Reloading Caddy..."
    sudo systemctl reload caddy
    
    echo ""
    echo "✅ MCP endpoint added!"
    echo ""
    echo "Your services:"
    echo "  🏘  https://agentictown.rach.es (AgenticTown)"
    echo "  🎲  https://dice.rach.es (Dice Oracle)"
    echo "  🏒  https://hubsports.rach.es (HubSports REST API)"
    echo "  🤖  https://hubsports-mcp.rach.es (HubSports Official MCP)"
else
    echo "❌ Configuration validation failed!"
    exit 1
fi

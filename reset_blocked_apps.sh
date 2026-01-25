#!/bin/bash
cat > blocked_apps.json << 'EOF'
[
    "discord",
    "slack",
    "steam",
    "brave",
    "firefox",
    "signal"
]
EOF
echo "Created/reset blocked_apps.json"

#!/bin/bash
cat > blocked_apps.json << 'EOF'
[
    "brave",
    "discord",
    "firefox",
    "signal",
    "slack",
    "steam"
]
EOF
echo "Created/reset blocked_apps.json"

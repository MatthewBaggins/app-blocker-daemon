#!/bin/bash
# Installation script for App Blocker Daemon

set -e

REPO_PATH=$(pwd)
PYTHON_PATH=$(which python3)

echo "Installing App Blocker Daemon..."

# Set up systemd service
sed "s|REPO_PATH_PLACEHOLDER|$REPO_PATH|g; s|PYTHON_PATH_PLACEHOLDER|$PYTHON_PATH|g" app-blocker-daemon.service > ~/.config/systemd/user/app-blocker-daemon.service

# Make daemon executable
chmod +x daemon.py

# Make .env
if [ ! -f .env ]; then
  cp .env.example .env
fi

# Create default blocked apps file config if it doesn't exist
if [ ! -f default_blocked_apps.json ]; then
cat > default_blocked_apps.json << 'EOF'
  [
    "brave",
    "discord",
    "firefox",
    "signal",
    "slack",
    "steam"
  ]
EOF
echo "Created default_blocked_apps.json"
fi

# Create blocked apps file config if it doesn't exist
if [ ! -f blocked_apps.json ]; then
  ./reset_blocked_apps.sh
fi

# Enable and start the service
systemctl --user daemon-reload
systemctl --user enable --now app-blocker-daemon.service

echo "Installation complete!"
systemctl --user status app-blocker-daemon.service

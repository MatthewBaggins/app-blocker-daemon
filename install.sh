#!/bin/bash
# Installation script for App Blocker Daemon

set -e

REPO_PATH=$(pwd)

echo "Installing Site Blocker app daemon..."

# Set up systemd service
sed "s|REPO_PATH_PLACEHOLDER|$REPO_PATH|g" site-blocker.service > ~/.config/systemd/user/site-blocker.service

# Make daemon executable
chmod +x daemon.py

# Create config if it doesn't exist
if [ ! -f config.json ]; then
  cat > config.json << 'EOF'
{
  "blocked_apps": [
    "Discord",
    "slack",
    "steam",
    "brave",
    "brave-browser",
    "firefox"
  ],
  "check_interval": 0.5
}
EOF
  echo "Created config.json"
fi

# Enable and start the service
systemctl --user daemon-reload
systemctl --user enable --now site-blocker.service

echo "Installation complete!"
systemctl --user status site-blocker.service

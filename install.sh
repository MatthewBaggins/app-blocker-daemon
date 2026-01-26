#!/bin/bash
# Installation script for App Blocker Daemon

set -e

REPO_PATH=$(pwd)

echo "Installing Site Blocker app daemon..."

# Set up systemd service
sed "s|REPO_PATH_PLACEHOLDER|$REPO_PATH|g" site-blocker.service > ~/.config/systemd/user/site-blocker.service

# Make daemon executable
chmod +x daemon.py

# Creat default blocked apps file config if it doesn't exist
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
systemctl --user enable --now site-blocker.service

echo "Installation complete!"
systemctl --user status site-blocker.service

#!/bin/bash
# Uninstallation script for App Blocker Daemon

set -e

echo "Uninstalling Site Blocker app daemon..."

systemctl --user stop site-blocker.service
systemctl --user disable site-blocker.service
rm ~/.config/systemd/user/site-blocker.service
systemctl --user daemon-reload

echo "Uninstallation complete!"

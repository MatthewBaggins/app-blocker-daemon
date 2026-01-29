#!/bin/bash
# Uninstallation script for App Blocker Daemon

set -e

echo "Uninstalling App Blocker Daemon..."

systemctl --user stop app-blocker-daemon.service
systemctl --user disable app-blocker-daemon.service
rm ~/.config/systemd/user/app-blocker-daemon.service
systemctl --user daemon-reload

echo "Uninstallation complete!"

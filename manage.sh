#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
usage: $0 <command>

commands:
  install              install the app
  uninstall            remove the app
  reinstall            remove and install the app
  reset                restore blocked_apps.json to default_blocked_apps.json

  start                start the app
  stop                 stop the app
  restart              restart the app
  status               show status
  logs | daemon-logs   show last 20 messages from daemon logs
  service-logs         show service logs

  help                 show this message
EOF
}


install() {
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
  cat > default_blocked_apps.json << EOF
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
    cp default_blocked_apps.json blocked_apps.json && echo "Reset blocked_apps.json"
  fi

  # Enable and start the service
  systemctl --user daemon-reload
  systemctl --user enable --now app-blocker-daemon.service

  echo "Installation complete!"
  systemctl --user status app-blocker-daemon.service

}

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <mode>" >&2
  exit 1
fi

arg="$1"

uninstall() {
  echo "Uninstalling App Blocker Daemon..."
  systemctl --user stop app-blocker-daemon.service
  systemctl --user disable app-blocker-daemon.service
  rm ~/.config/systemd/user/app-blocker-daemon.service
  systemctl --user daemon-reload
  echo "Uninstallation complete!"
}

case "$arg" in
  install) install ;;
  uninstall) uninstall ;;
  reinstall) uninstall && echo "" && install ;;
  reset) cp default_blocked_apps.json blocked_apps.json && echo "Reset blocked_apps.json" ;;
  
  start) systemctl --user start app-blocker-daemon.service ;;
  stop) systemctl --user stop app-blocker-daemon.service ;;
  restart) systemctl --user stop app-blocker-daemon.service && systemctl --user start app-blocker-daemon.service ;;
  status) systemctl --user status app-blocker-daemon.service ;;
  logs|daemon-logs) cat logs/daemon.log | tail -n 20 ;;
  service-logs) journalctl --user -u app-blocker-daemon.service -f ;;
  
  help|h|--help|-h) usage ;;

  *) echo "invalid argument: $arg" >&2 && exit 2 ;;
esac

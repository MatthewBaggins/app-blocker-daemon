# App Blocker Daemon

Standalone daemon for blocking applications on Ubuntu.

## Install

From the repo root directory:

```bash
REPO_PATH=$(pwd)
sed "s|REPO_PATH_PLACEHOLDER|$REPO_PATH|g" site-blocker.service > ~/.config/systemd/user/site-blocker.service
chmod +x daemon.py
cat > config.json << 'EOF'
{
  "blocked_apps": [
    "Discord",
    "slack",
    "steam",
    "brave",
    "brave-browser",
    "firefox",
    "code"
  ],
  "check_interval": 0.5
}
EOF
systemctl --user daemon-reload
systemctl --user enable --now site-blocker.service
systemctl --user status site-blocker.service
```

## Configure

Edit `config.json`:

```json
{
  "blocked_apps": ["app_name", "another_app"],
  "check_interval": 0.5
}
```

To find app process names: `ps aux | grep -i appname`

Config changes auto-reload while running.

## Control

- Start: `systemctl --user start site-blocker.service`
- Stop: `systemctl --user stop site-blocker.service`
- Status: `systemctl --user status site-blocker.service`
- Logs: `journalctl --user -u site-blocker.service -f`

## Uninstall

```bash
systemctl --user stop site-blocker.service
systemctl --user disable site-blocker.service
rm ~/.config/systemd/user/site-blocker.service
systemctl --user daemon-reload
```

## Manual Run

```bash
./daemon.py
```

Or in background:
```bash
nohup ./daemon.py &
```

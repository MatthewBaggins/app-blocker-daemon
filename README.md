# App Blocker Daemon

Standalone daemon for blocking applications on Ubuntu.

## Install

Run `./install.sh`.

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

Run `./uninstall.sh`.

## Manual Run

```bash
./daemon.py
```

Or in background:
```bash
nohup ./daemon.py &
```

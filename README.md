# App Blocker Daemon

Standalone daemon for blocking applications on Ubuntu.

For a site-blocking Chromium/Brave extension, see [site-blocker](https://github.com/MatthewBaggins/site-blocker).

## Install etc

- Install: `./install.sh`
- Uninstall: `./uninstall.sh`
- Reinstall: `./reinstall.sh`
- Reset `blocked_apps.json` (to default settings): `./reset_blocked_apps.sh`

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

## Manual Run

```bash
./daemon.py
```

Or in background:

```bash
nohup ./daemon.py &
```

`blocked_apps.json` is reset on every boot to the default defined in `reset_blocked_apps.sh`.
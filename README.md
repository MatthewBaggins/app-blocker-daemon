# App Blocker Daemon

A daemon for blocking applications on Ubuntu.

For a site-blocking Chromium/Brave extension, see [site-blocker](https://github.com/MatthewBaggins/site-blocker).

## Install etc

- Install: `./install.sh`
- Uninstall: `./uninstall.sh`
- Reinstall: `./reinstall.sh`
- Reset `blocked_apps.json` (to default settings): `./reset_blocked_apps.sh`

## Configure

### Environment Variables

Create a `.env` file in the project root with:

```env
BLOCKED_APPS_CHECK_INTERVAL=1
BLOCKED_APPS_RESET_INTERVAL=60
```

### Blocked Apps

Edit `blocked_apps.json`:

```json
["app_name", "another_app"]
```

To find app process names: `ps aux | grep -i appname`

Blocked apps file changes auto-reload while running.

## Control

- Start: `systemctl --user start app-blocker-daemon.service`
- Stop: `systemctl --user stop app-blocker-daemon.service`
- Status: `systemctl --user status app-blocker-daemon.service`
- Logs: `journalctl --user -u app-blocker-daemon.service -f`

## Manual Run

```bash
./daemon.py
```

Or in background:

```bash
nohup ./daemon.py
```

`blocked_apps.json` is reset on every boot to the default defined in `reset_blocked_apps.sh`. It also resets every minute (except for the apps that are currently running).

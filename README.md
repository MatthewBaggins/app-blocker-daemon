# App Blocker Daemon

A daemon for blocking applications on Ubuntu.

For a site-blocking Chromium/Brave extension, see [site-blocker](https://github.com/MatthewBaggins/site-blocker).

## Install etc

(You need give the permission to each script to execute it this way via `chmod +x <script-name`>. Otherwise, you can execute them with bash: `bash <script-name>`.)

- Install: `./install.sh` (this is the only one that needs to be executable for installation to work)
- Uninstall: `./uninstall.sh`
- Reinstall: `./reinstall.sh`
- Reset `blocked_apps.json` (to default settings): `./reset_blocked_apps.sh`
- View logs: `./logs.sh`
- View status: `./status.sh`

## Configure

### Environment Variables

Create a `.env` file in the project root with:

```env
CHECK_TICK=1
RESET_TICK=60
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

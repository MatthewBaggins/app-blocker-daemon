# App Blocker Daemon

Standalone daemon for blocking applications on Ubuntu.

## Installation etc

- Install: `./install.sh`
- Uninstall: `./uninstall.sh`
- Reinstall: `./reinstall.sh`
- Reset config (to default settings): `./reset_config.sh`
  
## Control

- Start: `systemctl --user start site-blocker.service`
- Stop: `systemctl --user stop site-blocker.service`
- Status: `systemctl --user status site-blocker.service`
- Logs: `journalctl --user -u site-blocker.service -f`


## Configure

Edit `config.json`:

```json
{
  "blocked_apps": ["app_name", "another_app"],
  "check_interval": 0.5
}
```

To find app process names: `ps aux | grep -i appname`

Config changes auto-reload while running, with the checking time determined by `check_interval`.

## Manual Run

```bash
./daemon.py
```

Or in background:

```bash
nohup ./daemon.py &
```

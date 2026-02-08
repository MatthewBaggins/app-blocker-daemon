# App Blocker Daemon

A daemon for blocking applications on Ubuntu.

For a site-blocking Chromium/Brave extension, see [site-blocker](https://github.com/MatthewBaggins/site-blocker).

## How it works

- Every `CHECK_TICK` seconds (defined in `.env`), it reads `blocked_apps.txt` and kills the apps that match the names listed in there. It also re-reads `.env` to update its values of `CHECK_TICK` and `RESET_TICK`.
- Every `RESET_TICK` seconds (defined in `.env`), it resets `blocked_apps.txt` to `default_blocked_apps.txt`, *except* those apps listed in `default_blocked_apps.txt` that are currently active.
- Detailed logs of the app's behavior can be found in `logs/daemon.log`.

## Install and Manage

Use the `manage.sh` script to install, uninstall, and manage the app. Ensure the script has execute permissions (`chmod +x manage.sh`) or run it with `bash`.

The most important commands are:

- `./manage.sh install` (it will make the app start on every subsquent boot, until uninstalled)
- `./manage.sh uninstall`
- `./manage.sh reinstall`
- `./manage.sh reset` - reset `blocked_apps.txt` to `default_blocked_apps.txt` (except for those apps in `default_blocked_apps.txt` that are currently running)

For more commands (perhaps somewhat helpful in debugging), see `./manage.sh help`.

### Alternative: Manual Run

```bash
./daemon.py
```

Or in background:

```bash
nohup ./daemon.py
```

Or using python (sometimes useful for easy debugging):

```python
python daemon.py
```

## Configure

### Environment Variables

Create a `.env` file in the project root with:

```bash
CHECK_TICK=1 # the daemon loads the settings, kills apps that are being blocked, etc, every **second**
RESET_TICK=300 # blocked_apps.txt is reset to default_blocked_apps.txt every 300 seconds = 5 minutes
```

Running `./manage.sh install` copies `.env.example` to `.env`.

Not strictly necessary (the daemon has hard-coded fallback defaults equal to the ones shown above), but recommended.

### Blocked Apps

Edit `blocked_apps.txt` and `default_blocked_apps.txt`:

```txt
app_name
another_app
```

`blocked_apps.txt` is read every `CHECK_TICK` seconds. It is reset to `default_blocked_apps.txt` (except the apps in the latter that are currently active) every `RESET_TICK` seconds.

Running `./manage.sh install` copies `default_blocked_apps.txt` to `blocked_apps.txt`. If `default_blocked_apps.txt` happens not to exist, for whatever reason, it is created to a list hard-coded in `./manage.sh`.

To find app process names: `ps aux | grep -i appname`

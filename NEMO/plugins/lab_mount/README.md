# NEMO Lab Data Mount Plugin

This Django-based plugin for NEMO-CE (version 8.0.2) sends HTTP requests to a local fileserver daemon when users start and end lab tool usage sessions.

## Features
- **Auto-initialization**: Logs initialization on startup.
- **Dynamic Probing**: Automatically logs available Django and NEMO signal modules for transparency and troubleshooting.
- **Robust Client**: Calls `/mount` on tool login/occupation and `/unmount` on tool logout/release with `timeout=5`.
- **Graceful Error Handling**: Catches exceptions and logs them without crashing the host NEMO application.
- **Configurable**: Configured via environment variables or Django settings.

---

## Installation

Add `"nemo.plugins.lab_mount"` to the `INSTALLED_APPS` list in `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps ...
    "NEMO.plugins.fileserver_plugin",
    "nemo.plugins.lab_mount",
]
```

---

## Configuration

The plugin uses the following environment variables or Django settings:

| Environment Variable | Django Settings Key | Description | Default |
|---|---|---|---|
| `LAB_DAEMON_URL` | `LAB_DAEMON_URL` | Base URL of the daemon service | `http://127.0.0.1:5000` |
| `LAB_DAEMON_TIMEOUT` | `LAB_DAEMON_TIMEOUT` | Connection timeout in seconds | `5` |

---

## Troubleshooting

1. Check NEMO container or service stdout/stderr log output. Look for:
   - `LabDataMountPlugin initialized`
   - `Successfully registered lab_mount signals`
2. If the fileserver is down or unreachable, look for errors containing:
   - `Error communicating with daemon` or `Daemon unreachable`
   - These errors are logged as warnings/errors, but **will not crash** or block NEMO operations.

---

## Manual Verification

Run a django shell using:
```bash
python manage.py shell
```

Paste the following Python code snippet to trigger mock mount/unmount requests:

```python
from nemo.models import UsageEvent, User, Tool, Project

# Fetch mock data
user = User.objects.first()
tool = Tool.objects.first()
project = Project.objects.first()

# 1. Trigger Mount (Session Start)
event = UsageEvent.objects.create(user=user, tool=tool, project=project)

# 2. Trigger Unmount (Session End)
event.end = event.start
event.save()
```

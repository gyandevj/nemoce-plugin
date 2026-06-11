# Lab Data Mount Plugin – Features

## Core Features

- **Auto-mount on login** – When a user starts using a tool in NEMO, their personal folder appears on that tool's computer automatically
- **Auto-unmount on logout** – When the user finishes, their folder disappears. Nothing left behind on shared machines
- **User isolation** – Each researcher sees only their own folder. No accidental access to其他人's data

## Directory Structure

- **User folders** – `/srv/labdata/users/[netid]` – Private, only that user can access
- **Group folders** – `/srv/labdata/groups/[groupname]` – Shared with everyone in the same lab group (uses POSIX ACLs)
- **Public folder** – `/srv/labdata/public/` – Read-only, always available, for lab protocols and templates

## Security

- **HMAC authentication** – All plugin-to-daemon requests are signed with a shared secret
- **Timestamp validation** – Requests expire after 30 seconds, preventing replay attacks
- **Path sanitization** – No `/../` or special characters allowed in user/tool names
- **API key in environment** – Never hardcoded in config files

## Session Management

- **JSON session persistence** – Active sessions saved to disk, survives daemon restarts
- **File locking** – `fcntl.flock` prevents concurrent write corruption
- **Orphan recovery** – On startup, finds and cleans up any mounts left over from crashed sessions
- **REST API** – `GET /sessions` to see who's logged in where

## Disk Quotas

- **Per-user limits** – 10GB soft, 12GB hard (configurable)
- **Enforced at write time** – Users can't exceed their quota
- **Quota checking** – `GET /quota/[user]` endpoint to check usage

## Idle Monitoring

- **Open file detection** – Uses `lsof` to check if any files are still open before unmounting
- **Graceful wait** – Waits up to 30 seconds for active writes to finish
- **Ghost session prevention** – If user logs back in during the wait window, unmount is cancelled
- **Lazy unmount fallback** – `umount -l` after timeout if files won't close

## Samba Integration

- **Bind mounts** – User folders appear inside Samba shares without copying files
- **Per-tool shares** – Each tool has its own share pointing to its session directory
- **VPN access** – Remote users can mount the same folder over Princeton VPN
- **Windows Explorer friendly** – Folders appear/disappear on refresh, no extra software needed

## Logging & Monitoring

- **Color console output** – Green for mounts, magenta for unmounts, red for errors
- **File logging** – Daily rotation, 30-day retention
- **Health check** – `GET /health` endpoint for monitoring
- **Audit trail** – All mount/unmount actions logged with timestamps

## Error Handling

- **No NEMO crashes** – Plugin catches all exceptions, logs them, and continues
- **Idempotent operations** – Mounting twice is safe (returns "already mounted")
- **Graceful failure** – If daemon is down, plugin logs error but doesn't break NEMO

## Production Ready

- **systemd service file** – Daemon starts on boot and restarts on failure
- **Configurable paths** – Everything in `/srv/labdata/` (standard Linux location)
- **Root under sandbox** – Daemon runs as root but with systemd restrictions
- **No hardcoded IPs** – All configuration via environment variables

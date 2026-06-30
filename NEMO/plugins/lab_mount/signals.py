import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from NEMO.models import UsageEvent, User

# Support both lowercase and uppercase imports of the client module
try:
    from nemo.plugins.lab_mount.client import DaemonClient
except ModuleNotFoundError:
    from NEMO.plugins.lab_mount.client import DaemonClient
import os
import requests
from django.conf import settings

logger = logging.getLogger(__name__)
daemon_url = os.environ.get("FILESERVER_DAEMON_URL", "https://localhost:5000")
cert_path = os.environ.get("LAB_MOUNT_CERT_PATH")
key_path = os.environ.get("LAB_MOUNT_KEY_PATH")
ca_path = os.environ.get("LAB_MOUNT_CA_PATH")

cert = (cert_path, key_path) if cert_path and key_path else None
verify = ca_path if ca_path else True

# Fallback to local dev certs if they exist
if not cert:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    project_root = os.path.dirname(base_dir)
    dev_cert = os.path.join(project_root, "lab-daemon", "certs", "client.crt")
    dev_key = os.path.join(project_root, "lab-daemon", "certs", "client.key")
    dev_ca = os.path.join(project_root, "lab-daemon", "certs", "ca.crt")
    if os.path.exists(dev_cert) and os.path.exists(dev_key):
        cert = (dev_cert, dev_key)
        verify = dev_ca

client = DaemonClient(daemon_url, cert=cert, verify=verify)



@receiver(post_save, sender=UsageEvent)
def on_usage_event_saved(sender, instance, created, **kwargs):
    """
    Signal handler for UsageEvent post_save.

    On creation of an active usage event, triggers a mount for the specific
    project the user selected at check-in:
      - my_files/  -> /srv/labdata/users/u{user_id}
      - my_groups/account_{account_id}/project_{project_id}/ -> specific project dir
      - public/    -> /srv/labdata/public (read-only)

    On update where end timestamp is set, triggers unmount.
    """
    try:
        user_id = instance.user.id
        username = instance.user.username
        tool_name = instance.tool.name

        # Extract project and account IDs from the selected project.
        # UsageEvent.project is the project the user checked into.
        project_id = instance.project.id if instance.project else None
        # account_id is a direct FK on the Project model.
        account_id = instance.project.account_id if instance.project else None

        logger.debug(
            f"UsageEvent saved: user={username} (ID: {user_id}), tool={tool_name}, "
            f"project={project_id}, account={account_id}, created={created}, end={instance.end}"
        )

        if created:
            if not instance.end:
                if project_id is None or account_id is None:
                    logger.warning(
                        f"UsageEvent created for user '{username}' on '{tool_name}' but no project "
                        f"was selected (project={project_id}, account={account_id}). Skipping mount."
                    )
                    return
                logger.info(
                    f"UsageEvent created (active session) for user '{username}' (ID: {user_id}) "
                    f"on tool '{tool_name}' with project {project_id} / account {account_id}. Calling mount."
                )
                success = client.mount(user_id, tool_name, account_id, project_id)
                logger.info(f"Mount command result: {success}")
            else:
                logger.info(
                    f"UsageEvent created but already ended for user '{username}' on tool "
                    f"'{tool_name}'. Skipping mount."
                )
        else:
            # It's an update — check if the session is ending.
            if instance.end:
                if project_id is None or account_id is None:
                    logger.warning(
                        f"UsageEvent ended for user '{username}' on '{tool_name}' but project "
                        f"info missing. Skipping unmount."
                    )
                    return
                logger.info(
                    f"UsageEvent updated (session ended) for user '{username}' (ID: {user_id}) "
                    f"on tool '{tool_name}' with project {project_id} / account {account_id}. Calling unmount."
                )
                success = client.unmount(user_id, tool_name, account_id, project_id)
                logger.info(f"Unmount command result: {success}")
            else:
                logger.debug(
                    f"UsageEvent updated but session still active (no end date) for user "
                    f"'{username}' on tool '{tool_name}'."
                )
    except Exception as e:
        logger.error(f"Error in on_usage_event_saved signal handler: {e}", exc_info=True)


@receiver(post_save, sender=User)
def provision_nextcloud_user(sender, instance, created, **kwargs):
    """
    On user creation in Django, trigger NextCloud OCS API to create account.
    """
    if created:
        url = f"{settings.NEXTCLOUD_URL}/ocs/v1.php/cloud/users"
        headers = {
            "OCS-APIRequest": "true",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        auth = (settings.NEXTCLOUD_ADMIN_USER, settings.NEXTCLOUD_ADMIN_PASSWORD)

        # NextCloud expects userid, password, email, and displayname.
        payload = {
            "userid": instance.username,
            "password": "dev",
            "email": instance.email,
            "displayName": f"{instance.first_name} {instance.last_name}"
        }

        try:
            logger.info(f"Syncing new user '{instance.username}' (ID: {instance.id}) to NextCloud...")
            resp = requests.post(url, data=payload, headers=headers, auth=auth, timeout=10, verify=False)
            if resp.status_code in (200, 201):
                logger.info(f"Successfully provisioned NextCloud user: {instance.username}")
            else:
                logger.error(f"Failed to provision NextCloud user. Code: {resp.status_code}, Response: {resp.text}")
        except Exception as e:
            logger.error(f"Error calling NextCloud Provisioning API: {e}")

        # Initialize directory on the file server daemon
        try:
            client.initialize_user(instance.id)
        except Exception as e:
            logger.error(f"Failed to request directory initialization for user ID {instance.id}: {e}")

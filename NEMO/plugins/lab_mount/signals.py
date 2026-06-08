import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from NEMO.models import UsageEvent

# Support both lowercase and uppercase imports of the client module
try:
    from nemo.plugins.lab_mount.client import DaemonClient
except ModuleNotFoundError:
    from NEMO.plugins.lab_mount.client import DaemonClient

logger = logging.getLogger(__name__)
client = DaemonClient("http://127.0.0.1:5000")


@receiver(post_save, sender=UsageEvent)
def on_usage_event_saved(sender, instance, created, **kwargs):
    """
    Signal handler for UsageEvent post_save.
    On creation of active usage event, triggers mount.
    On update where end timestamp is set, triggers unmount.
    """
    try:
        username = instance.user.username
        tool_name = instance.tool.name
        print(f"!!! NEMO SENDING: user={username}, tool={tool_name}, created={created}")

        logger.debug(f"UsageEvent saved signal received: user={username}, tool={tool_name}, created={created}, end={instance.end}")
        
        if created:
            if not instance.end:
                logger.info(f"UsageEvent created (active session) for user '{username}' on tool '{tool_name}'. Calling mount.")
                success = client.mount(username, tool_name)
                logger.info(f"Mount command result: {success}")
            else:
                logger.info(f"UsageEvent created but already ended for user '{username}' on tool '{tool_name}'. Skipping mount.")
        else:
            # It's an update. Check if the session is ending
            if instance.end:
                logger.info(f"UsageEvent updated (session ended) for user '{username}' on tool '{tool_name}'. Calling unmount.")
                success = client.unmount(username, tool_name)
                logger.info(f"Unmount command result: {success}")
            else:
                logger.debug(f"UsageEvent updated but session is still active (no end date) for user '{username}' on tool '{tool_name}'.")
    except Exception as e:
        logger.error(f"Error in on_usage_event_saved signal handler: {e}", exc_info=True)

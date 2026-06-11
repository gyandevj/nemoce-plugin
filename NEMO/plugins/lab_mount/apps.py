import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

class LabMountConfig(AppConfig):
    name = "NEMO.plugins.lab_mount"
    verbose_name = "Lab Data Mount Config"

    def ready(self):
        logger.info("LabDataMountPlugin initialized")

        # Read configuration (e.g. from settings)
        daemon_url = getattr(settings, "LAB_DAEMON_URL", "http://143.244.144.91:5000")
        logger.info(f"Lab Data Mount plugin daemon URL: {daemon_url}")

        # Dynamic Signal Discovery
        self.discover_signals()

        # Import/register signals
        try:
            import nemo.plugins.lab_mount.signals
            logger.info("Successfully registered lab_mount signals (lowercase nemo)")
        except ModuleNotFoundError:
            try:
                import NEMO.plugins.lab_mount.signals
                logger.info("Successfully registered lab_mount signals (uppercase NEMO)")
            except Exception as e:
                logger.error(f"Failed to register lab_mount signals: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to register lab_mount signals: {e}", exc_info=True)

    def discover_signals(self):
        """
        Dynamically probe for signals to log availability and debug.
        """
        logger.info("Probing for signals...")
        
        # Probe for Django auth signals
        try:
            from django.contrib.auth import signals as auth_signals
            logger.info(f"Django Auth Signals: {[s for s in dir(auth_signals) if not s.startswith('_')]}")
        except Exception as e:
            logger.warning(f"Could not inspect django.contrib.auth.signals: {e}")

        # Probe for Django model signals
        try:
            from django.db.models import signals as model_signals
            logger.info(f"Django Model Signals: {[s for s in dir(model_signals) if not s.startswith('_')]}")
        except Exception as e:
            logger.warning(f"Could not inspect django.db.models.signals: {e}")

        # Fallback signal discovery search
        nemo_signals_paths = [
            "nemo.signals",
            "NEMO.signals",
            "nemo.tools.signals",
            "NEMO.tools.signals"
        ]
        
        for path in nemo_signals_paths:
            try:
                mod = __import__(path, fromlist=["*"])
                available_attrs = [attr for attr in dir(mod) if not attr.startswith("_")]
                logger.info(f"Successfully loaded '{path}' signal module. Available attributes: {available_attrs}")
            except ModuleNotFoundError:
                logger.debug(f"Signal module '{path}' not found.")
            except Exception as e:
                logger.error(f"Unexpected error importing '{path}': {e}")

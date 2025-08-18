"""Main JupyterHub configuration file.

This file orchestrates loading all configuration modules.
"""

import os
import sys

from berdlhub.config.validators import validate_environment

# Add config directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Get the config object
c = get_config()  # noqa: F821 Provided by JupyterHub at runtime; not defined in this file.

# Validate environment variables first

validate_environment()

# Load all configuration modules in order
from berdlhub.config.hub import configure_hub  # noqa: E402
from berdlhub.config.auth import configure_auth  # noqa: E402
from berdlhub.config.spawner import configure_spawner  # noqa: E402
from berdlhub.config.profiles import configure_profiles  # noqa: E402
from berdlhub.config.storage import configure_hostpath_storage  # noqa: E402
from berdlhub.config.environment import configure_environment  # noqa: E402
from berdlhub.config.services import configure_services  # noqa: E402
from berdlhub.config.debug import configure_debug  # noqa: E402
from berdlhub.config.hooks import configure_hooks  # noqa: E402

# Apply configurations in dependency order
configure_hub(c)
configure_auth(c)
configure_spawner(c)
configure_environment(c)
configure_hostpath_storage(c)
configure_profiles(c)
configure_services(c)
configure_hooks(c)

# Apply debug last (can override other settings)
configure_debug(c)

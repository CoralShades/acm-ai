"""Service start/stop control — reuses existing scripts/ modules."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to sys.path so we can import the shared modules
_scripts_dir = str(Path(__file__).resolve().parent.parent.parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from _health_monitor import (  # noqa: E402
    ServiceStatus,
    check_health,
    get_detailed_health,
    poll_all_health,
)
from _port_utils import (  # noqa: E402
    PortConflict,
    check_all_ports,
    find_port_owner,
    is_port_in_use,
    kill_port_owner,
)
from _process_utils import (  # noqa: E402
    is_docker_available,
    is_service_running,
    start_service_background,
    stop_service,
)
from _service_config import (  # noqa: E402
    SHUTDOWN_ORDER,
    STARTUP_ORDER,
    ServiceDef,
    get_services,
)

__all__ = [
    "ServiceStatus",
    "ServiceDef",
    "PortConflict",
    "STARTUP_ORDER",
    "SHUTDOWN_ORDER",
    "get_services",
    "check_health",
    "poll_all_health",
    "get_detailed_health",
    "is_docker_available",
    "is_service_running",
    "start_service_background",
    "stop_service",
    "check_all_ports",
    "find_port_owner",
    "is_port_in_use",
    "kill_port_owner",
]

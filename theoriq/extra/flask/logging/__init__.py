import logging
from typing import Optional

from .system_health_filter import SystemHealthFilter
from ...log_utils import init


def init_logging(level: Optional[str] = None):
    init(level)
    logger = logging.getLogger("werkzeug")
    logger.addFilter(SystemHealthFilter())

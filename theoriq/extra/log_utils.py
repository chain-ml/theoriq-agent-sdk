import logging
import os
from typing import Optional


def init(level: Optional[str]):
    effective_level = level or os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(level=effective_level)

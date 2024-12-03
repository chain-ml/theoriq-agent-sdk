import logging
import os
from typing import Optional

from . import execute_context, http_request_context


def init(level: Optional[str]):
    effective_level = level or os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(
        level=effective_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(x_request_id)s - %(theoriq_request_id)s - %(message)s",
    )

    record_factory = execute_context.get_record_factory(logging.getLogRecordFactory())
    record_factory = http_request_context.get_record_factory(record_factory)
    logging.setLogRecordFactory(record_factory)

import logging
import os
from typing import Any, Optional, Union

from . import execute_context, http_request_context


def init(level: Optional[Union[str, int]], force: bool = False) -> None:
    effective_level = level or os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(
        level=effective_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(x_request_id)s - %(theoriq_request_id)s - %(message)s",
        force=force,
    )

    record_factory = execute_context.get_record_factory(logging.getLogRecordFactory())
    record_factory = http_request_context.get_record_factory(record_factory)
    logging.setLogRecordFactory(record_factory)


class LogfmtFormatter(logging.Formatter):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="test",
            args=(),
            exc_info=None)
        self._default_fields = vars(record).keys()

    def format(self, record):
        # Get basic log record attributes
        base_info = {
            'time': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        for (key, value) in record.__dict__.items():
            if key not in self._default_fields and value is not None:
                base_info[key] = value

        # Format as logfmt (key=value pairs)
        logfmt_str = ' '.join([f'{k}={LogfmtFormatter._quote_value(v)}' for k, v in base_info.items()])

        # Add exception info if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            logfmt_str += f' exception="{exc_text}"'

        return logfmt_str

    @staticmethod
    def _quote_value(value):
        """Quote values that contain spaces or special characters"""
        value_str = str(value)
        if ' ' in value_str or '=' in value_str or '"' in value_str:
            # Escape quotes and wrap in quotes
            value_str = value_str.replace('"', '\\"')
            return f'"{value_str}"'
        return value_str

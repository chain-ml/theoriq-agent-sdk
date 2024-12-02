import logging


class SystemHealthFilter(logging.Filter):
    def __init__(self):
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if "/system/livez" in message and "200" in message and "GET" in message:
            record.levelno = logging.DEBUG
            record.levelname = "DEBUG"
            return logging.getLogger().isEnabledFor(logging.DEBUG)
        return True

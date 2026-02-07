import logging


class DefaultLogger:
    def __init__(self, level: int = logging.INFO):
        self.log = logging.getLogger("pbapi")
        self.log.setLevel(level)

        # Ensure the root logger is configured if not already
        if not logging.root.handlers:
            logging.basicConfig(level=level)
            for handler in logging.root.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setLevel(logging.WARNING)

    def info(self, msg: str, *args, **kwargs):
        self.log.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.log.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.log.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self.log.debug(msg, *args, **kwargs)

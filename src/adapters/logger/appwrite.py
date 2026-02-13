import logging

from src.adapters.logger.default import DefaultLogger


class AppwriteHandler(logging.Handler):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def emit(self, record):
        try:
            msg = self.format(record)
            if record.levelno >= logging.ERROR:
                self.context.error(msg)
            else:
                self.context.log(msg)
        except Exception:
            self.handleError(record)


class AppwriteLogger(DefaultLogger):
    def __init__(self, context, level: int = logging.INFO):
        super().__init__(level)
        self.context = context

        # Check if AppwriteHandler is already attached to avoid duplicates
        if not any(isinstance(h, AppwriteHandler) for h in self.log.handlers):
            handler = AppwriteHandler(context)
            handler.setLevel(level)
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            self.log.addHandler(handler)

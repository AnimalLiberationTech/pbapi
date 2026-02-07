import logging

from starlette.requests import Request


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


def get_logger(request: Request, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("pbapi")

    if "appwrite_context" in request.scope:
        context = request.scope["appwrite_context"]
        # Check if AppwriteHandler is already attached to avoid duplicates
        if not any(isinstance(h, AppwriteHandler) for h in logger.handlers):
            handler = AppwriteHandler(context)
            handler.setLevel(level)
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    return logger

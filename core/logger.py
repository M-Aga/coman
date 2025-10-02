from rich.logging import RichHandler
import logging, os
def get_logger(name: str):
    level = os.getenv("COMAN_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(message)s", datefmt="[%X]",
                        handlers=[RichHandler(rich_tracebacks=True)])
    return logging.getLogger(name)

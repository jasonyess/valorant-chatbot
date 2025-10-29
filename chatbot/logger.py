import logging
import sys

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("chat")
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [CHATBOT] %(message)s"))
    logger.addHandler(handler)
    return logger
import logging
import sys
from typing import NamedTuple

MitmLoggers = NamedTuple("MitmLoggers", [("config", logging.Logger), ("xmpp", logging.Logger)])

# TODO: maybe separate the logger creating functions?
def setup_loggers() -> MitmLoggers:
    config_logger = logging.getLogger("mitm-config")
    xmpp_logger = logging.getLogger("mitm-xmpp")

    # set log targets
    config_handler = logging.StreamHandler(sys.stdout)
    xmpp_handler = logging.StreamHandler(sys.stdout)

    # set log levels
    config_logger.setLevel(logging.DEBUG)
    config_handler.setLevel(logging.INFO)

    xmpp_logger.setLevel(logging.DEBUG)
    xmpp_handler.setLevel(logging.DEBUG)

    # set log formatters
    config_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [CONFIG-MITM] %(message)s"))
    xmpp_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [XMPP-MITM] %(message)s"))

    config_logger.addHandler(config_handler)
    xmpp_logger.addHandler(xmpp_handler)

    return MitmLoggers(config=config_logger, xmpp=xmpp_logger)

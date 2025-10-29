from dotenv import load_dotenv
load_dotenv()

import asyncio
import threading
import mitm
import chatbot
import time
from typing import Callable, Awaitable

if mitm.client.is_riot_running():
    raise Exception("Riot Client is running")

mitm_loggers = mitm.setup_loggers()
chatbot_logger = chatbot.logger.setup_logger()

config_mitm = mitm.ConfigMITM("127.0.0.1", 8008, mitm_loggers.config)
threading.Thread(target=config_mitm.start, daemon=True).start()

conversations: dict[str, chatbot.Conversation] = {}

async def on_chat(sender: str, message: str, message_callback: Callable[[str], Awaitable]):
    conv = conversations.get(sender)

    if conv is None:
        conv = chatbot.Conversation(chatbot_logger)
        conversations[sender] = conv

    conv.add_user_message(message)

    time.sleep(3)

    resp = conv.get_response()
    if not resp: return
    await message_callback(resp)

xmpp_mitm = mitm.XmppMITM("0.0.0.0", 35478, mitm_loggers.xmpp, on_chat)

xmpp_mitm.chat_responder = on_chat
threading.Thread(target=lambda: asyncio.run(xmpp_mitm.start()), daemon=True).start()

mitm.client.launch_riot_client(config_mitm.host, config_mitm.port)
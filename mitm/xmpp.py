import asyncio
import logging
import ssl
import time
import os
from typing import NamedTuple, Optional, Callable, Awaitable
from xml.etree import ElementTree
from .shared import affinity_mappings

SocketConnection = NamedTuple("SocketConnection", [
    ("reader", asyncio.StreamReader),
    ("writer", asyncio.StreamWriter),
])

class XmppMITM():
    def __init__(self, host: str, port: int, logger: logging.Logger, chat_handler: Callable[[str, str, Callable[[str], Awaitable]], Awaitable]):
        self.host = host
        self.port = port
        self.logger = logger
        self.chat_handler = chat_handler

    async def start(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile="certs\\server.cert", keyfile="certs\\server.key")

        game_tcp = await asyncio.start_server(lambda reader, writer: XmppConnection(self.logger, self.chat_handler).handle_stream(SocketConnection(reader=reader, writer=writer)), self.host, self.port, ssl=ssl_context)
        self.logger.info(f"Listening on {self.host}:{self.port}")

        async with game_tcp:
            await game_tcp.serve_forever()

# an instance of an xmpp connection with the game and Riot servers
# this is separate from `XmppMITM` so these can run concurrently
class XmppConnection():
    def __init__(self, logger: logging.Logger, chat_handler = Callable[[str, str, Callable[[str], Awaitable]], Awaitable]):
        self.logger = logger
        self.chat_handler = chat_handler

    async def handle_stream(self, conn: SocketConnection):
        addr = conn.writer.get_extra_info("sockname")[0]

        self.logger.info(f"Incoming connection {addr}")

        self.game_conn = conn
        self.riot_conn = await self.open_riot_connection(addr)

        if not self.riot_conn:
            self.logger.error("Failed to connect to Riot host, closing connection")

            conn.writer.close()
            await conn.writer.wait_closed()

            return

        asyncio.create_task(self.poll_game_conn())
        asyncio.create_task(self.poll_riot_conn())

    async def poll_game_conn(self):
        self.logger.info("Polling game connection for data")
        
        try:
            while data := await self.game_conn.reader.read(4096):
                self.logger.debug(f"Outgoing data {data!r}")
                self.riot_conn.writer.write(data)
        except Exception as e:
            self.logger.error(f"An error occurred while polling game stream\n{e}")
        finally:
            self.riot_conn.writer.close()
            await self.riot_conn.writer.wait_closed()

    async def poll_riot_conn(self):
        self.logger.info("Polling Riot connection for data")

        try:
            while data := await self.riot_conn.reader.read(4096):
                self.logger.debug(f"Incoming data f{data!r}")
                self.game_conn.writer.write(data)

                try:
                    root = ElementTree.fromstring(data)
                    body = root.find("body")

                    if not body is None:
                        if root.find("muc:x/muc:item", {
                            "muc": "http://jabber.org/protocol/muc#user"
                        }).get("jid") == os.environ["SENDER_JID"]: continue # TODO: THIS SHOUDLNT BE HARD CODED

                        # the incoming data is a chat message
                        await self.chat_handler(root.get("from"), body.text, lambda msg: self.send_message(root, msg))
                        self.logger.info(f"Received and handled incoming chat message: {body.text}")
                except ElementTree.ParseError:
                    # TODO: this is often raised because chunked data isn't handled properly
                    self.logger.warning("Received invalid XML")
        except Exception as e:
            self.logger.error(f"An error occurred while polling Riot stream\n{e}")
        finally:
            self.game_conn.writer.close()
            await self.game_conn.writer.wait_closed()

    async def send_message(self, root: ElementTree.Element, message: str):
        write_data = f"<message id='{time.time() * 1000}:1' to='{root.get("from")}' type='{root.get("type")}'><body>{message}</body></message>"

        self.riot_conn.writer.write(write_data.encode("utf-8"))
        await self.riot_conn.writer.drain()
        
        self.logger.info("Sent response " + write_data)

    async def open_riot_connection(self, addr: str) -> Optional[SocketConnection]:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        mapping = affinity_mappings.by_local_host(addr)

        if not mapping:
            self.logger.error(f"Failed to map local address '{addr}' to Riot host")
            return

        reader, writer = await asyncio.open_connection(
            host=mapping["riot_host"],
            port=mapping["riot_port"],
            ssl=ssl_context,
        )

        self.logger.info(f"Connected to {mapping["riot_host"]}:{mapping["riot_port"]}")

        return SocketConnection(reader=reader, writer=writer)
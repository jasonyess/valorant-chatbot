import logging
import json
import http.server
import http.client
from .shared import affinity_mappings

class ConfigMITM():
    def __init__(self, host: str, port: int, logger: logging.Logger):
        self.host = host
        self.port = port
        self.logger = logger

    def start(self):
        server = http.server.HTTPServer((self.host, self.port), lambda *args, **kwargs: ConfigHttpHandler(self.logger, *args, **kwargs))

        self.logger.info(f"Listening on http://{self.host}:{self.port}")

        server.serve_forever()

class ConfigHttpHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, logger: logging.Logger, *args, **kwargs):
        self.logger = logger
        super().__init__(*args, **kwargs)

    def handle_one_request(self):
        self.raw_requestline = self.rfile.readline(65537)
        if not self.raw_requestline:
            self.close_connection = True
            return
        
        if not self.parse_request(): return

        self.logger.info(f"Outgoing {self.command} {self.path}")

        # forward request upstream
        conn = http.client.HTTPSConnection("clientconfig.rpg.riotgames.com", 443)

        headers = {k: v for k, v in self.headers.items() if k.lower() not in ["host", "accept-encoding"]}
        headers["host"] = "clientconfig.rpg.riotgames.com"
        
        conn.request(self.command, self.path, headers=headers)

        res = conn.getresponse()
        res_data = res.read()
        conn.close()

        self.logger.debug(f"Forwarded upstream {res_data}")

        # rewrite chat endpoints to be our own
        if res.status == 200 and self.path.startswith("/api/v1/config/player"):
            res_json = json.loads(res_data)
            
            for region, ip in res_json["chat.affinities"].items():
                mapping = affinity_mappings.get_or_create(ip, res_json["chat.port"])
                res_json["chat.affinities"][region] = mapping["local_host"]

            res_json["chat.port"] = 35478 # TODO: move this to be defined in main.py somewhere
            res_json["chat.host"] = "127.0.0.1" # TODO: this too
            res_json["chat.allow_bad_cert.enabled"] = True # idk if this is necessary

            res_data = json.dumps(res_json).encode("utf-8")

        # return proxied response
        self.send_response(res.status)

        for k, v in self.headers.items():
            self.send_header(k, v)
        self.end_headers()

        self.wfile.write(res_data)

        self.logger.info(f"Incoming {res.status}")

"""HTTP + WS Transport classes and functions."""

from aiohttp import web
from aries_cloudagent.transport.inbound.base import BaseInboundTransport
from aries_cloudagent.transport.inbound import http, ws


class HttpWsTransport(BaseInboundTransport):
    """Http+Ws Transport class."""

    def __init__(self, host: str, port: int, create_session, **kwargs) -> None:
        """
        Initialize an inbound HTTP transport instance.

        Args:
            host: Host to listen on
            port: Port to listen on
            create_session: Method to create a new inbound session

        """
        super().__init__("http+ws", create_session, **kwargs)
        self.host = host
        self.port = port
        self.site: web.BaseSite = None

    inbound_ws_message_handler = ws.WsTransport.inbound_message_handler
    inbound_http_message_handler = http.HttpTransport.inbound_message_handler
    start = http.HttpTransport.start
    stop = http.HttpTransport.stop
    heartbeat_interval = None
    timout_interval = None

    async def make_application(self) -> web.Application:
        """Construct the aiohttp application."""
        app_args = {}
        if self.max_message_size:
            app_args["client_max_size"] = self.max_message_size
        app = web.Application(**app_args)
        app.add_routes([web.get("/", self.inbound_ws_message_handler)])
        app.add_routes([web.post("/", self.inbound_http_message_handler)])
        return app

"""Admin-trustping protocol."""
import re

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.event_bus import Event, EventBus
from aries_cloudagent.core.profile import Profile
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.storage.error import StorageNotFoundError
from aries_cloudagent.protocols.trustping.v1_0.messages.ping import Ping
from marshmallow import fields

from .util import (
    ExceptionReporter,
    admin_only,
    generate_model_schema,
    get_connection,
    send_to_admins,
)


ADMIN_PROTOCOL_URI = (
    "https://github.com/hyperledger/"
    "aries-toolbox/tree/master/docs/admin-trustping/0.1"
)
SEND = f"{ADMIN_PROTOCOL_URI}/send"
SENT = f"{ADMIN_PROTOCOL_URI}/sent"
RESPONSE_RECEIVED = f"{ADMIN_PROTOCOL_URI}/response-received"

MESSAGE_TYPES = {
    SEND: "acapy_plugin_toolbox.trustping.Send",
    SENT: "acapy_plugin_toolbox.trustping.Sent",
    RESPONSE_RECEIVED: "acapy_plugin_toolbox.trustping.ResponseReceived",
}

TRUSTPING_EVENT_PATTERN = re.compile("^acapy::ping::response_received$")


async def setup(context: InjectionContext, protocol_registry: ProtocolRegistry = None):
    """Setup the trustping plugin."""
    if not protocol_registry:
        protocol_registry = context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)

    event_bus = context.inject(EventBus)
    event_bus.subscribe(TRUSTPING_EVENT_PATTERN, trust_ping_response_received)


async def trust_ping_response_received(profile: Profile, event: Event):
    message = ResponseReceived(connection_id=event.payload["connection_id"])
    responder = profile.inject(BaseResponder)
    await send_to_admins(profile, message, responder)


ResponseReceived, ResponseReceivedSchema = generate_model_schema(
    name="ResponseReceived",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=RESPONSE_RECEIVED,
    schema={
        "connection_id": fields.Str(required=True),
    },
)


Send, SendSchema = generate_model_schema(
    name="Send",
    handler="acapy_plugin_toolbox.trustping.SendHandler",
    msg_type=SEND,
    schema={
        "connection_id": fields.Str(required=True),
        "comment": fields.Str(required=True),
    },
)


Sent, SentSchema = generate_model_schema(
    name="Sent",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=SENT,
    schema={
        "connection_id": fields.Str(required=True),
    },
)


class SendHandler(BaseHandler):
    """Handler for received send requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send requests."""
        # pylint: disable=protected-access
        connection_record = None
        async with context.session() as session:
            # Checking connection id is valid
            async with ExceptionReporter(
                responder, StorageNotFoundError, context.message
            ):
                await get_connection(session, context.message.connection_id)
        ping = Ping(comment=context.message.comment)
        await responder.send(ping, connection_id=context.message.connection_id)
        sent_msg = Sent(connection_id=context.message.connection_id)
        sent_msg.assign_thread_from(context.message)
        await responder.send_reply(sent_msg)

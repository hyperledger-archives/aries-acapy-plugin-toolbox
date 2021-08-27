"""Trust ping protocol"""

import re
from .util import admin_only, generate_model_schema, send_to_admins
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.profile import ProfileSession, Profile
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.core.event_bus import Event, EventBus
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.messaging.decorators.localization_decorator import (
    LocalizationDecorator,
)
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.messaging.valid import INDY_ISO8601_DATETIME
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError
from marshmallow import fields

from aries_cloudagent.protocols.trustping.v1_0.messages.ping import Ping


ADMIN_PROTOCOL_URI = (
    "https://github.com/hyperledger/"
    "aries-toolbox/tree/master/docs/admin-trustping/0.1"
)
SEND = f"{ADMIN_PROTOCOL_URI}/send"
RESPONSE_RECEIVED = f"{ADMIN_PROTOCOL_URI}/response-received"

MESSAGE_TYPES = {
    SEND: "acapy_plugin_toolbox.trustping.Send",
    RESPONSE_RECEIVED: "acapy_plugin_toolbox.trustping.ResponseReceived",
}

TRUSTPING_EVENT_PATTERN = re.compile("^acapy::trustping::received$")


async def setup(context: InjectionContext, protocol_registry: ProblemReport = None):
    """Setup the trustping plugin."""
    if not protocol_registry:
        protocol_registry = context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)

    event_bus = context.inject(EventBus)
    event_bus.subscribe(TRUSTPING_EVENT_PATTERN, trust_ping_event_handler)


async def trust_ping_event_handler(profile: Profile, event: Event):
    """
    Handle trust ping events.

    Send a notification to admins when trust pings are received.
    """

    msg: TrustPingRecord = TrustPingRecord.deserialize(event.payload)
    msg.state = TrustPingRecord.STATE_RECV

    notification = ResponseReceived(
        connection_id=event.payload["connection_id"], message=msg
    )

    responder = profile.inject(BaseResponder)
    async with profile.session() as session:
        await msg.save(session, reason="Trust ping")
        await send_to_admins(session, notification, responder, to_session_only=True)


class TrustPingRecord(BaseRecord):
    """Trust Ping Record."""

    # pylint: disable=too-few-public-methods

    RECORD_ID_NAME = "record_id"
    RECORD_TYPE = "trustping"

    STATE_SENT = "sent"
    STATE_RECV = "recv"

    class Meta:
        """TrustPing metadata."""

        schema_class = "TrustPingRecordSchema"

    def __init__(
        self,
        *,
        record_id: str = None,
        connection_id: str = None,
        message_id: str = None,
        locale: str = None,
        content: str = None,
        sent_time: str = None,
        state: str = None,
        **kwargs,
    ):
        """Initialize a new SchemaRecord."""
        super().__init__(record_id, state or self.STATE_SENT, **kwargs)
        self.connection_id = connection_id
        self.message_id = message_id
        self.locale = locale
        self.content = content
        self.sent_time = sent_time

    @property
    def record_id(self) -> str:
        """Accessor for this schema's id."""
        return self._id

    @property
    def record_value(self) -> dict:
        """Get record value."""
        return {
            prop: getattr(self, prop)
            for prop in ("content", "locale", "sent_time", "state")
        }

    @property
    def record_tags(self) -> dict:
        """Get tags for record."""
        return {"connection_id": self.connection_id, "message_id": self.message_id}

    @classmethod
    async def retrieve_by_message_id(
        cls, session: ProfileSession, message_id: str
    ) -> "TrustPingRecord":
        """Retrieve a trust ping record by message id."""
        return await cls.retrieve_by_tag_filter(session, {"message_id": message_id})


class TrustPingRecordSchema(BaseRecordSchema):
    """Schema to allow serialization/deserialization of TrustPing
    records.
    """

    # pylint: disable=too-few-public-methods

    class Meta:
        """TrustPingRecordSchema metadata."""

        model_class = TrustPingRecord

    connection_id = fields.Str(required=False)
    message_id = fields.Str(required=False)
    sent_time = fields.Str(required=False, **INDY_ISO8601_DATETIME)
    locale = fields.Str(required=False)
    content = fields.Str(required=False)


Send, SendTrustPing = generate_model_schema(
    name="Send",
    handler="acapy_plugin_toolbox.trustping.SendHandler",
    msg_type=SEND,
    schema={
        "connection_id": fields.Str(required=True),
        "content": fields.Str(required=True),
    },
)


ResponseReceived, ResponseReceivedSchema = generate_model_schema(
    name="RespondReceived",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=f"{ADMIN_PROTOCOL_URI}/sent",
    schema={
        "connection_id": fields.Str(required=True),
        "message": fields.Nested(
            TrustPingRecordSchema,
            exclude=["created_at", "updated_at"],
            required=True,
        ),
    },
)


class SendHandler(BaseHandler):
    """Handler for received send requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send requests."""
        # pylint: disable=protected-access
        session = await context.session()
        try:
            connection = await ConnRecord.retrieve_by_id(
                session, context.message.connection_id
            )
        except StorageNotFoundError:
            report = ProblemReport(
                description={"en": "Connection not found."}, who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        msg = Ping(
            content=context.message.content,
            localization=LocalizationDecorator(locale="en"),
        )

        await responder.send(msg, connection_id=context.message.connection_id)

        record = TrustPingRecord(
            connection_id=context.message.connection_id,
            message_id=msg._id,
            sent_time=msg.sent_time,
            content=msg.content,
            state=TrustPingRecord.STATE_SENT,
        )
        await record.save(session, reason="Trust ping received.")
        sent_msg = ResponseReceived(
            connection_id=connection.connection_id, message=record
        )
        sent_msg.assign_thread_from(context.message)
        await responder.send_reply(sent_msg)

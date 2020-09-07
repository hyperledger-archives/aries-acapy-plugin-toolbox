"""BasicMessage Plugin."""
# pylint: disable=invalid-name, too-few-public-methods

from typing import Union
from datetime import datetime

from marshmallow import fields

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.connections.models.connection_record import (
    ConnectionRecord
)
from aries_cloudagent.messaging.base_handler import (
    BaseHandler, BaseResponder, RequestContext
)
from aries_cloudagent.messaging.decorators.localization_decorator import (
    LocalizationDecorator
)
from aries_cloudagent.messaging.models.base_record import (
    BaseRecord, BaseRecordSchema
)
from aries_cloudagent.messaging.valid import INDY_ISO8601_DATETIME
from aries_cloudagent.protocols.connections.v1_0.manager import ConnectionManager
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError

from .util import (
    generate_model_schema, admin_only, timestamp_utc_iso, datetime_from_iso
)

PROTOCOL_URI = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/basicmessage/1.0"
BASIC_MESSAGE = f"{PROTOCOL_URI}/message"

ADMIN_PROTOCOL_URI = "https://github.com/hyperledger/" \
    "aries-toolbox/tree/master/docs/admin-basicmessage/0.1"
GET = f"{ADMIN_PROTOCOL_URI}/get"
SEND = f"{ADMIN_PROTOCOL_URI}/send"
DELETE = f"{ADMIN_PROTOCOL_URI}/delete"
NEW = f"{ADMIN_PROTOCOL_URI}/new"

MESSAGE_TYPES = {
    BASIC_MESSAGE: 'acapy_plugin_toolbox.basicmessage.BasicMessage',
    GET: 'acapy_plugin_toolbox.basicmessage.Get',
    SEND: 'acapy_plugin_toolbox.basicmessage.Send',
    DELETE: 'acapy_plugin_toolbox.basicmessage.Delete'
}


async def setup(
        context: InjectionContext,
        protocol_registry: ProblemReport = None
):
    """Setup the basicmessage plugin."""
    if not protocol_registry:
        protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )


class BasicMessageRecord(BaseRecord):
    """BasicMessage Record."""
    # pylint: disable=too-few-public-methods

    RECORD_ID_NAME = "record_id"
    RECORD_TYPE = "basicmessage"

    STATE_SENT = 'sent'
    STATE_RECV = 'recv'

    class Meta:
        """BasicMessage metadata."""

        schema_class = "BasicMessageRecordSchema"

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
            **kwargs):
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
            for prop in (
                'content',
                'locale',
                'sent_time',
                'state',
            )
        }

    @property
    def record_tags(self) -> dict:
        """Get tags for record."""
        return {
            'connection_id': self.connection_id,
            'message_id': self.message_id
        }

    @classmethod
    async def retrieve_by_message_id(
            cls,
            context: InjectionContext,
            message_id: str) -> "BasicMessageRecord":
        """Retrieve a basic message record by message id."""
        return await cls.retrieve_by_tag_filter(
            context,
            {'message_id': message_id}
        )


class BasicMessageRecordSchema(BaseRecordSchema):
    """Schema to allow serialization/deserialization of BasicMessage
    records.
    """
    # pylint: disable=too-few-public-methods

    class Meta:
        """BasicMessageRecordSchema metadata."""

        model_class = BasicMessageRecord

    connection_id = fields.Str(required=False)
    message_id = fields.Str(required=False)
    sent_time = fields.Str(required=False, **INDY_ISO8601_DATETIME)
    locale = fields.Str(required=False)
    content = fields.Str(required=False)


def basic_message_init(
        self,
        *,
        sent_time: Union[str, datetime] = None,
        content: str = None,
        localization: str = None,
        **kwargs,
):
    """
    Initialize basic message object.

    Args:
        sent_time: Time message was sent
        content: message content
        localization: localization

    """
    # pylint: disable=protected-access
    super(BasicMessage, self).__init__(**kwargs)
    if not sent_time:
        sent_time = timestamp_utc_iso()
    if localization:
        self._decorators["l10n"] = localization
    self.sent_time = sent_time
    self.content = content


BasicMessage, BasicMessageSchema = generate_model_schema(
    name='BasicMessage',
    handler='acapy_plugin_toolbox.basicmessage.BasicMessageHandler',
    msg_type=BASIC_MESSAGE,
    schema={
        'sent_time': fields.Str(
            required=False,
            description="Time message was sent, ISO8601",
            **INDY_ISO8601_DATETIME,
        ),
        'content': fields.Str(
            required=True,
            description="Message content",
            example="Hello",
        )
    },
    init=basic_message_init
)


New, NewSchema = generate_model_schema(
    name='New',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=NEW,
    schema={
        'connection_id': fields.Str(required=True),
        'message': fields.Nested(
            BasicMessageRecordSchema,
            exclude=['created_at', 'updated_at'],
            required=True
        )
    }
)


class BasicMessageHandler(BaseHandler):
    """Handler for received Basic Messages."""
    # pylint: disable=protected-access

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received basic message."""
        msg = BasicMessageRecord(
            connection_id=context.connection_record.connection_id,
            message_id=context.message._id,
            sent_time=context.message.sent_time,
            content=context.message.content,
            state=BasicMessageRecord.STATE_RECV
        )
        await msg.save(context, reason='New message received.')

        await responder.send_webhook(
            "basicmessages",
            {
                "connection_id": context.connection_record.connection_id,
                "message_id": context.message._id,
                "content": context.message.content,
                "state": "received",
            },
        )

        connection_mgr = ConnectionManager(context)
        admins = await ConnectionRecord.query(
            context, post_filter_positive={'their_role': 'admin'}
        )

        if not admins:
            return

        admins = filter(lambda admin: admin.state == 'active', admins)
        admin_verkeys = [
            target.recipient_keys[0]
            for admin in admins
            for target in await connection_mgr.get_connection_targets(
                connection=admin
            )
        ]

        notification = New(
            connection_id=context.connection_record.connection_id,
            message=msg
        )

        for verkey in admin_verkeys:
            await responder.send(
                notification,
                reply_to_verkey=verkey,
                to_session_only=True
            )


Get, GetSchema = generate_model_schema(
    name='Get',
    handler='acapy_plugin_toolbox.basicmessage.GetHandler',
    msg_type=GET,
    schema={
        'connection_id': fields.Str(required=False),
        'limit': fields.Int(required=False),
        'offset': fields.Int(required=False)
    }
)


MessageList, MessageListSchema = generate_model_schema(
    name='MessageList',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=f'{ADMIN_PROTOCOL_URI}/messages',
    schema={
        'connection_id': fields.Str(required=False),
        'messages': fields.List(fields.Nested(
            BasicMessageRecordSchema,
            exclude=['created_at', 'updated_at']
        )),
        'offset': fields.Int(required=False),
        'count': fields.Int(required=False),
        'remaining': fields.Int(required=False),
    }
)


class GetHandler(BaseHandler):
    """Handler for received get requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get requests."""
        tag_filter = dict(filter(lambda item: item[1] is not None, {
            'connection_id': context.message.connection_id,
        }.items()))
        msgs = sorted(
            await BasicMessageRecord.query(
                context,
                tag_filter
            ),
            key=lambda msg: datetime_from_iso(msg.sent_time),
            reverse=True
        )
        count = len(msgs)
        offset = 0
        if (
                context.message.offset and
                context.message.offset > 0 and
                context.message.offset < count
        ):
            offset = context.message.offset
            count = count - offset

        if (
                context.message.limit and
                context.message.limit > 0 and
                context.message.limit < count
        ):
            count = context.message.limit

        remaining = len(msgs) - offset - count
        msgs = msgs[offset:offset+count]
        msg_list = MessageList(
            connection_id=context.message.connection_id,  # None when not given
            messages=msgs,
            offset=offset,
            count=count,
            remaining=remaining
        )
        msg_list.assign_thread_from(context.message)
        await responder.send_reply(msg_list)


Send, SendSchema = generate_model_schema(
    name='Send',
    handler='acapy_plugin_toolbox.basicmessage.SendHandler',
    msg_type=SEND,
    schema={
        'connection_id': fields.Str(required=True),
        'content': fields.Str(required=True)
    }
)


Sent, SentSchema = generate_model_schema(
    name='Sent',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=f'{ADMIN_PROTOCOL_URI}/sent',
    schema={
        'connection_id': fields.Str(required=True),
        'message': fields.Nested(
            BasicMessageRecordSchema,
            exclude=['created_at', 'updated_at'],
            required=True
        )
    }
)


class SendHandler(BaseHandler):
    """Handler for received send requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send requests."""
        # pylint: disable=protected-access
        try:
            connection = await ConnectionRecord.retrieve_by_id(
                context, context.message.connection_id
            )
        except StorageNotFoundError:
            report = ProblemReport(
                explain_ltxt='Connection not found.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        msg = BasicMessage(
            content=context.message.content,
            localization=LocalizationDecorator(locale='en')
        )

        await responder.send(msg, connection_id=connection.connection_id)

        record = BasicMessageRecord(
            connection_id=context.message.connection_id,
            message_id=msg._id,
            sent_time=msg.sent_time,
            content=msg.content,
            state=BasicMessageRecord.STATE_SENT
        )
        await record.save(context, reason='Message sent.')
        sent_msg = Sent(connection_id=connection.connection_id, message=record)
        sent_msg.assign_thread_from(context.message)
        await responder.send_reply(sent_msg)


Delete, DeleteSchema = generate_model_schema(
    name='Delete',
    handler='acapy_plugin_toolbox.basicmessage.DeleteHandler',
    msg_type=DELETE,
    schema={
        'connection_id': fields.Str(required=False),
        'message_id': fields.Str(required=False),
        'before_date': fields.Str(required=False),
        'return_deleted': fields.Bool(required=False, missing=True)
    }
)


Deleted, DeletedSchema = generate_model_schema(
    name='Deleted',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=f'{ADMIN_PROTOCOL_URI}/deleted',
    schema={
        'connection_id': fields.Str(required=False),
        'deleted': fields.List(fields.Nested(
            BasicMessageRecordSchema,
            exclude=['created_at', 'updated_at'],
            required=False
        )),
    }
)


class DeleteHandler(BaseHandler):
    """Handler for received delete requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received delete requests."""
        tag_filter = dict(filter(lambda item: item[1] is not None, {
            'connection_id': context.message.connection_id,
            'message_id': context.message.message_id,
        }.items()))
        msgs = await BasicMessageRecord.query(
            context,
            tag_filter
        )
        if context.message.before_date:
            msgs = list(filter(
                lambda msg: datetime_from_iso(msg.sent_time) <
                datetime_from_iso(context.message.before_date),
                msgs
            ))

        for msg in msgs:
            await msg.delete_record(context)

        ack = Deleted(
            connection_id=context.message.connection_id,
            deleted=msgs if context.message.return_deleted else None
        )
        ack.assign_thread_from(context.message)
        await responder.send_reply(ack)

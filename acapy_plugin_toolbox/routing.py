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

from aries_cloudagent.protocols.routing.models.route_update import RouteUpdate

from .util import (
    generate_model_schema, admin_only, timestamp_utc_iso, datetime_from_iso
)

ADMIN_PROTOCOL_URI = "https://github.com/hyperledger/" \
    "aries-toolbox/tree/master/docs/admin-routing/0.1"
SEND_UPDATE = f"{ADMIN_PROTOCOL_URI}/send_update"

MESSAGE_TYPES = {
    SEND_UPDATE: 'acapy_plugin_toolbox.routing.send_update',

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


SendUpdate, SendUpdateSchema = generate_model_schema(
    name='SendUpdate',
    handler='acapy_plugin_toolbox.routing.send_update',
    msg_type=SEND_UPDATE,
    schema={
        'connection_id': fields.Str(required=True),
        'verkey': fields.Str(required=True),
        'action': fields.Str(required=True),
    }
)


class SendUpdate(BaseHandler):
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

        msg = RouteUpdate(
            content=context.message.content,
            localization=LocalizationDecorator(locale='en')
        )

        await responder.send(msg, connection_id=connection.connection_id)

        ack.assign_thread_from(context.message)
        await responder.send_reply(ack)

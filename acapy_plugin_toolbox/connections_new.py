"""Define messages for connections admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import fields, validate

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import BaseHandler, BaseResponder, RequestContext
from aries_cloudagent.protocols.connections.manager import ConnectionManager
from aries_cloudagent.connections.models.connection_record import (
    ConnectionRecord, ConnectionRecordSchema
)
from aries_cloudagent.protocols.connections.messages.connection_invitation import (
    ConnectionInvitation,
)
from aries_cloudagent.protocols.problem_report.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError

from .util import generate_model_schema, admin_only

PROTOCOL = 'https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1'

# Message Types
GET_LIST = '{}/get-list'.format(PROTOCOL)
LIST = '{}/list'.format(PROTOCOL)
GET = '{}/get'.format(PROTOCOL)
CONNECTION = '{}/connection'.format(PROTOCOL)
UPDATE = '{}/update'.format(PROTOCOL)
DELETE = '{}/delete'.format(PROTOCOL)
DELETED = '{}/deleted'.format(PROTOCOL)

# Message Type string to Message Class map
MESSAGE_TYPES = {
    GET_LIST:
        'acapy_plugin_toolbox.connections'
        '.GetList',
    LIST:
        'acapy_plugin_toolbox.connections'
        '.List',
    # GET:
    #     'acapy_plugin_toolbox.connections'
    #     '.Get',
    UPDATE:
        'acapy_plugin_toolbox.connections'
        '.Update',
    CONNECTION:
        'acapy_plugin_toolbox.connections'
        '.Connnection',
    DELETE:
        'acapy_plugin_toolbox.connections'
        '.Delete',
    DELETED:
        'acapy_plugin_toolbox.connections'
        '.Deleted',
}


async def setup(context: InjectionContext):
    """Setup the connections plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )


GetList, GetListSchema = generate_model_schema(
    name='GetList',
    handler='acapy_plugin_toolbox.connections.GetListHandler',
    msg_type=GET_LIST,
    schema={
        'initiator': fields.Str(
            validate=validate.OneOf(['self', 'external']),
            required=False,
        ),
        'invitation_key': fields.Str(required=False),
        'my_did': fields.Str(required=False),
        'state': fields.Str(
            validate=validate.OneOf([
                'init',
                'invitation',
                'request',
                'response',
                'active',
                'error',
                'inactive'
            ]),
            required=False
        ),
        'their_did': fields.Str(required=False),
        'their_role': fields.Str(required=False)
    }
)

List, ListSchema = generate_model_schema(
    name='List',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=LIST,
    schema={
        'results': fields.List(
            fields.Nested(ConnectionRecordSchema),
            required=True
        )
    }
)


class GetListHandler(BaseHandler):
    """Handler for get connection list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get connection list request."""

        def connection_sort_key(conn):
            """Get the sorting key for a particular connection."""
            if conn["state"] == ConnectionRecord.STATE_INACTIVE:
                pfx = "2"
            elif conn["state"] == ConnectionRecord.STATE_INVITATION:
                pfx = "1"
            else:
                pfx = "0"
            return pfx + conn["created_at"]

        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                'my_did': context.message.my_did,
                'their_did': context.message.their_did,
            }.items())
        )
        post_filter = dict(filter(
            lambda item: item[1] is not None,
            {
                'initiator': context.message.initiator,
                'state': context.message.state,
                'their_role': context.message.their_role
            }.items()
        ))
        records = await ConnectionRecord.query(context, tag_filter, post_filter)
        results = [record.serialize() for record in records]
        results.sort(key=connection_sort_key)
        connection_list = List(results=results)
        connection_list.assign_thread_from(context.message)
        await responder.send_reply(connection_list)


# Get, GetSchema = generate_model_schema(
#     name='Get',
#     handler='acapy_plugin_toolbox.connections.GetHandler',
#     msg_type=GET,
#     schema={
#         'connection_id': fields.Str(required=True)
#     }
# )

Update, UpdateSchema = generate_model_schema(
    name='Update',
    handler='acapy_plugin_toolbox.connections.UpdateHandler',
    msg_type=UPDATE,
    schema={
        'connection_id': fields.Str(required=True),
        'label': fields.Str(required=False),
        'role': fields.Str(required=False)
    }
)

Connection, ConnectionSchema = generate_model_schema(
    name='Connection',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=CONNECTION,
    schema={
        'connection': fields.Nested(ConnectionRecordSchema, required=True),
    }
)


class UpdateHandler(BaseHandler):
    """Handler for update connection request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle update connection request."""
        try:
            connection = await ConnectionRecord.retrieve_by_id(
                context,
                context.message.connection_id
            )
        except StorageNotFoundError:
            report = ProblemReport(
                explain_ltxt='Connection not found.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)

        new_label = context.message.label or connection.their_label
        connection.their_label = new_label
        new_role = context.message.role or connection.their_role
        connection.their_role = new_role
        await connection.save(context, reason="Update request received.")
        conn_response = Connection(connection=connection)
        conn_response.assign_thread_from(context.message)
        await responder.send_reply(conn_response)


Delete, DeleteSchema = generate_model_schema(
    name='Delete',
    handler='acapy_plugin_toolbox.connections.DeleteHandler',
    msg_type=DELETE,
    schema={
        'connection_id': fields.Str(required=True),
    }
)

Deleted, DeletedSchema = generate_model_schema(
    name='Deleted',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=DELETED,
    schema={}
)


class DeleteHandler(BaseHandler):
    """Handler for delete connection request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle delete connection request."""
        if context.message.connection_id == \
                context.connection_record.connection_id:

            report = ProblemReport(
                explain_ltxt='Current connection cannot be deleted.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        try:
            connection = await ConnectionRecord.retrieve_by_id(
                context,
                context.message.connection_id
            )
        except StorageNotFoundError:
            report = ProblemReport(
                explain_ltxt='Connection not found.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        await connection.delete_record(context)
        deleted = Deleted()
        deleted.assign_thread_from(context.message)
        await responder.send_reply(deleted)

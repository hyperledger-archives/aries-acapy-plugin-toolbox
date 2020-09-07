"""Define messages for connections admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from typing import Dict, Any

from marshmallow import Schema, fields, validate

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import BaseHandler, BaseResponder, RequestContext
from aries_cloudagent.protocols.connections.v1_0.manager import ConnectionManager
from aries_cloudagent.connections.models.connection_record import (
    ConnectionRecord
)
from aries_cloudagent.protocols.connections.v1_0.messages.connection_invitation import (
    ConnectionInvitation,
)
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError

from .util import generate_model_schema, admin_only

PROTOCOL = (
    'https://github.com/hyperledger/aries-toolbox/'
    'tree/master/docs/admin-connections/0.1'
)

# Message Types
GET_LIST = '{}/get-list'.format(PROTOCOL)
LIST = '{}/list'.format(PROTOCOL)
UPDATE = '{}/update'.format(PROTOCOL)
CONNECTION = '{}/connection'.format(PROTOCOL)
DELETE = '{}/delete'.format(PROTOCOL)
DELETED = '{}/deleted'.format(PROTOCOL)
RECEIVE_INVITATION = '{}/receive-invitation'.format(PROTOCOL)

# Message Type string to Message Class map
MESSAGE_TYPES = {
    GET_LIST: 'acapy_plugin_toolbox.connections.GetList',
    LIST: 'acapy_plugin_toolbox.connections.List',
    UPDATE: 'acapy_plugin_toolbox.connections.Update',
    CONNECTION: 'acapy_plugin_toolbox.connections.Connnection',
    DELETE: 'acapy_plugin_toolbox.connections.Delete',
    DELETED: 'acapy_plugin_toolbox.connections.Deleted',
    RECEIVE_INVITATION: 'acapy_plugin_toolbox.connections.'
                        'ReceiveInvitation',
}


async def setup(
        context: InjectionContext,
        protocol_registry: ProtocolRegistry = None
):
    """Setup the connections plugin."""
    if not protocol_registry:
        protocol_registry = await context.inject(ProtocolRegistry)

    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )


BaseConnectionSchema = Schema.from_dict({
    'label': fields.Str(required=True),
    'my_did': fields.Str(required=True),
    'connection_id': fields.Str(required=True),
    'state': fields.Str(
        validate=validate.OneOf([
            'pending',
            'active',
            'error'
        ]),
        required=True
    ),
    'their_did': fields.Str(required=False),  # May be missing if pending
    'role': fields.Str(required=False),
    'raw_repr': fields.Dict(required=False)
})

Connection, ConnectionSchema = generate_model_schema(
    name='Connection',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=CONNECTION,
    schema=BaseConnectionSchema
)


def conn_record_to_message_repr(conn: ConnectionRecord) -> Dict[str, Any]:
    """Map ConnectionRecord onto Connection."""
    def _state_map(state: str) -> str:
        if state in ('active', 'response'):
            return 'active'
        if state == 'error':
            return 'error'
        return 'pending'

    return {
        'label': conn.their_label,
        'my_did': conn.my_did,
        'their_did': conn.their_did,
        'state': _state_map(conn.state),
        'role': conn.their_role,
        'connection_id': conn.connection_id,
        'raw_repr': conn.serialize()
    }


GetList, GetListSchema = generate_model_schema(
    name='GetList',
    handler='acapy_plugin_toolbox.connections.GetListHandler',
    msg_type=GET_LIST,
    schema={
        'my_did': fields.Str(required=False),
        'state': fields.Str(
            validate=validate.OneOf([
                'pending',
                'active',
                'error',
            ]),
            required=False
        ),
        'their_did': fields.Str(required=False),
        'role': fields.Str(required=False)
    }
)


List, ListSchema = generate_model_schema(
    name='List',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=LIST,
    schema={
        'connections': fields.List(
            fields.Nested(BaseConnectionSchema),
            required=True
        )
    }
)


class GetListHandler(BaseHandler):
    """Handler for get connection list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get connection list request."""

        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                'my_did': context.message.my_did,
                'their_did': context.message.their_did,
            }.items())
        )
        post_filter_positive = dict(filter(
            lambda item: item[1] is not None,
            {
                'their_role': context.message.role
            }.items()
        ))
        # TODO: Filter on state (needs mapping back to ACA-Py connection states)
        records = await ConnectionRecord.query(
            context, tag_filter, post_filter_positive
        )
        results = [
            Connection(**conn_record_to_message_repr(record))
            for record in records
        ]
        connection_list = List(connections=results)
        connection_list.assign_thread_from(context.message)
        await responder.send_reply(connection_list)


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
        conn_response = Connection(
            **conn_record_to_message_repr(connection)
        )
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
    schema={
        'connection_id': fields.Str(required=True),
    }
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
        deleted = Deleted(connection_id=connection.connection_id)
        deleted.assign_thread_from(context.message)
        await responder.send_reply(deleted)


ReceiveInvitation, ReceiveInvitationSchema = generate_model_schema(
    name='ReceiveInvitation',
    handler='acapy_plugin_toolbox.connections.ReceiveInvitationHandler',
    msg_type=RECEIVE_INVITATION,
    schema={
        'invitation': fields.Str(required=True),
        'auto_accept': fields.Bool(
            missing=False
        )
    }
)


class ReceiveInvitationHandler(BaseHandler):
    """Handler for receive invitation request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle recieve invitation request."""
        connection_mgr = ConnectionManager(context)
        invitation = ConnectionInvitation.from_url(context.message.invitation)
        connection = await connection_mgr.receive_invitation(
            invitation,
            auto_accept=context.message.auto_accept
        )
        connection_resp = Connection(**conn_record_to_message_repr(connection))
        await responder.send_reply(connection_resp)

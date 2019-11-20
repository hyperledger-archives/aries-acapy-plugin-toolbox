"""Define messages for connections admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import fields, validate

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

PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-connections/0.1'

# Message Types
CONNECTION_GET_LIST = '{}/connection-get-list'.format(PROTOCOL)
CONNECTION_LIST = '{}/connection-list'.format(PROTOCOL)
CONNECTION_GET = '{}/connection-get'.format(PROTOCOL)
CONNECTION = '{}/connection'.format(PROTOCOL)
INVITATION_GET_LIST = '{}/invitation-get-list'.format(PROTOCOL)
INVITATION_LIST = '{}/invitation-list'.format(PROTOCOL)
CREATE_INVITATION = '{}/create-invitation'.format(PROTOCOL)
INVITATION = '{}/invitation'.format(PROTOCOL)
RECEIVE_INVITATION = '{}/receive-invitation'.format(PROTOCOL)
ACCEPT_INVITATION = '{}/accept-invitation'.format(PROTOCOL)
ACCEPT_REQUEST = '{}/accept-request'.format(PROTOCOL)
ESTABLISH_INBOUND = '{}/establish-inbound'.format(PROTOCOL)
DELETE_CONNECTION = '{}/delete'.format(PROTOCOL)
UPDATE_CONNECTION = '{}/update'.format(PROTOCOL)
CONNECTION_ACK = '{}/ack'.format(PROTOCOL)

# Message Type string to Message Class map
MESSAGE_TYPES = {
    CONNECTION_GET_LIST:
        'aca_plugin_toolbox.connections'
        '.ConnectionGetList',
    CONNECTION_LIST:
        'aca_plugin_toolbox.connections'
        '.ConnectionList',
    CONNECTION_GET:
        'aca_plugin_toolbox.connections'
        '.ConnectionGet',
    CONNECTION:
        'aca_plugin_toolbox.connections'
        '.Connnection',
    CREATE_INVITATION:
        'aca_plugin_toolbox.connections'
        '.CreateInvitation',
    INVITATION_GET_LIST:
        'aca_plugin_toolbox.connections'
        '.InvitationGetList',
    INVITATION:
        'aca_plugin_toolbox.connections'
        '.Invitation',
    RECEIVE_INVITATION:
        'aca_plugin_toolbox.connections'
        '.ReceiveInvitation',
    ACCEPT_INVITATION:
        'aca_plugin_toolbox.connections'
        '.AcceptInvitation',
    ACCEPT_REQUEST:
        'aca_plugin_toolbox.connections'
        '.AcceptRequest',
    ESTABLISH_INBOUND:
        'aca_plugin_toolbox.connections'
        '.EstablishInbound',
    DELETE_CONNECTION:
        'aca_plugin_toolbox.connections'
        '.DeleteConnection',
    CONNECTION_ACK:
        'aca_plugin_toolbox.connections'
        '.ConnectionAck',
    UPDATE_CONNECTION:
        'aca_plugin_toolbox.connections'
        '.UpdateConnection',
}


ConnectionGetList, ConnectionGetListSchema = generate_model_schema(
    name='ConnectionGetList',
    handler='aca_plugin_toolbox.connections.ConnectionGetListHandler',
    msg_type=CONNECTION_GET_LIST,
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

ConnectionList, ConnectionListSchema = generate_model_schema(
    name='ConnectionList',
    handler='aca_plugin_toolbox.util.PassHandler',
    msg_type=CONNECTION_LIST,
    schema={
        'results': fields.List(
            fields.Nested(ConnectionRecordSchema),
            required=True
        )
    }
)

ConnectionGet, ConnectionGetSchema = generate_model_schema(
    name='ConnectionGet',
    handler='aca_plugin_toolbox.connections.ConnectionGetHandler',
    msg_type=CONNECTION_GET,
    schema={
        'connection_id': fields.Str(required=True)
    }
)

Connection, ConnectionSchema = generate_model_schema(
    name='Connection',
    handler='aca_plugin_toolbox.util.PassHandler',
    msg_type=CONNECTION,
    schema={
        'connection': fields.Nested(ConnectionRecordSchema, required=True),
    }
)

InvitationGetList, InvitationGetListSchema = generate_model_schema(
    name='InvitationGetList',
    handler='aca_plugin_toolbox.connections.InvitationGetListHandler',
    msg_type=INVITATION_GET_LIST,
    schema={
        'initiator': fields.Str(
            validate=validate.OneOf(['self', 'external']),
            required=False,
        ),
        'invitation_key': fields.Str(required=False),
        'my_did': fields.Str(required=False),
        'their_did': fields.Str(required=False),
        'their_role': fields.Str(required=False)
    }
)

CreateInvitation, CreateInvitationSchema = generate_model_schema(
    name='CreateInvitation',
    handler='aca_plugin_toolbox.connections.CreateInvitationHandler',
    msg_type=CREATE_INVITATION,
    schema={
        'label': fields.Str(required=False),
        'role': fields.Str(required=False),
        'accept': fields.Str(
            required=False,
            validate=validate.OneOf(['none', 'auto'])
        ),
        'public': fields.Boolean(missing=False),
        'multi_use': fields.Boolean(missing=False)
    }
)

Invitation, InvitationSchema = generate_model_schema(
    name='Invitation',
    handler='aca_plugin_toolbox.util.PassHandler',
    msg_type=INVITATION,
    schema={
        'connection_id': fields.Str(required=True),
        'invitation': fields.Str(required=True),
        'invitation_url': fields.Str(required=True)
    }
)

InvitationList, InvitationListSchema = generate_model_schema(
    name='InvitationList',
    handler='aca_plugin_toolbox.util.PassHandler',
    msg_type=INVITATION_LIST,
    schema={
        'results': fields.List(fields.Dict(
            connection=fields.Nested(ConnectionSchema),
            invitation=fields.Nested(InvitationSchema)
        ))
    }
)

class CreateInvitationHandler(BaseHandler):
    """Handler for create invitation request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle create invitation request."""
        connection_mgr = ConnectionManager(context)
        connection, invitation = await connection_mgr.create_invitation(
            my_label=context.message.label,
            their_role=context.message.role,
            accept=context.message.accept,
            multi_use=bool(context.message.multi_use),
            public=bool(context.message.public),
        )
        invite_response = Invitation(
            connection_id=connection and connection.connection_id,
            invitation=invitation.serialize(),
            invitation_url=invitation.to_url(),
        )
        invite_response.assign_thread_from(context.message)
        await responder.send_reply(invite_response)


ReceiveInvitation, ReceiveInvitationSchema = generate_model_schema(
    name='ReceiveInvitation',
    handler='aca_plugin_toolbox.connections.ReceiveInvitationHandler',
    msg_type=RECEIVE_INVITATION,
    schema={
        'invitation': fields.Str(required=True),
        'accept': fields.Str(
            validate=validate.OneOf(['none', 'auto']),
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
            invitation, accept=context.message.accept
        )
        connection_resp = Connection(connection=connection)
        await responder.send_reply(connection_resp)


AcceptInvitation, AcceptInvitationSchema = generate_model_schema(
    name='AcceptInvitation',
    handler='aca_plugin_toolbox.connections.AcceptInvitationHandler',
    msg_type=ACCEPT_INVITATION,
    schema={
        'connection_id': fields.Str(required=True),
        'my_endpoint': fields.Str(required=False),
        'my_label': fields.Str(required=False),
    }
)

AcceptRequest, AcceptRequestSchema = generate_model_schema(
    name='AcceptRequest',
    handler='aca_plugin_toolbox.connections.AcceptRequestHandler',
    msg_type=ACCEPT_REQUEST,
    schema={
        'connection_id': fields.Str(required=True),
        'my_endpoint': fields.Str(required=False),
    }
)

EstablishInbound, EstablishInboundSchema = generate_model_schema(
    name='EstablishInbound',
    handler='aca_plugin_toolbox.connections.EstablishInboundHandler',
    msg_type=ESTABLISH_INBOUND,
    schema={
        'connection_id': fields.Str(required=True),
        'ref_id': fields.Str(required=True),
    }
)

DeleteConnection, DeleteConnectionSchema = generate_model_schema(
    name='DeleteConnection',
    handler='aca_plugin_toolbox.connections.DeleteConnectionHandler',
    msg_type=DELETE_CONNECTION,
    schema={
        'connection_id': fields.Str(required=True),
    }
)

ConnectionAck, ConnectionAckSchema = generate_model_schema(
    name='ConnectionAck',
    handler='aca_plugin_toolbox.util.PassHandler',
    msg_type=CONNECTION_ACK,
    schema={}
)

UpdateConnection, UpdateConnectionSchema = generate_model_schema(
    name='UpdateConnection',
    handler='aca_plugin_toolbox.connections.UpdateConnectionHandler',
    msg_type=UPDATE_CONNECTION,
    schema={
        'connection_id': fields.Str(required=True),
        'label': fields.Str(required=False),
        'role': fields.Str(required=False)
    }
)


class DeleteConnectionHandler(BaseHandler):
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
        ack = ConnectionAck()
        ack.assign_thread_from(context.message)
        await responder.send_reply(ack)


class UpdateConnectionHandler(BaseHandler):
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


class ConnectionGetListHandler(BaseHandler):
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
        results = []
        for record in records:
            row = record.serialize()
            row["activity"] = await record.fetch_activity(context)
            results.append(row)
        results.sort(key=connection_sort_key)
        connection_list = ConnectionList(results=results)
        connection_list.assign_thread_from(context.message)
        await responder.send_reply(connection_list)


class InvitationGetListHandler(BaseHandler):
    """Handler for get invitation list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get invitation list request."""

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
                'state': 'invitation',
                'their_role': context.message.their_role
            }.items()
        ))
        records = await ConnectionRecord.query(context, tag_filter, post_filter)
        results = []
        for connection in records:
            try:
                invitation = await connection.retrieve_invitation(context)
            except StorageNotFoundError:
                continue

            row = {
                'connection': connection.serialize(),
                'invitation': {
                    'connection_id': connection and connection.connection_id,
                    'invitation': invitation.serialize(),
                    'invitation_url': invitation.to_url(),
                }
            }
            results.append(row)

        invitation_list = InvitationList(results=results)
        invitation_list.assign_thread_from(context.message)
        await responder.send_reply(invitation_list)

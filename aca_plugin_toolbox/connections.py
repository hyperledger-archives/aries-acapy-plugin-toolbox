"""Define messages for connections admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import fields, validate

from . import generate_model_schema, admin_only
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ..connections.manager import ConnectionManager
from ..connections.models.connection_record import (
    ConnectionRecord, ConnectionRecordSchema
)
from ..connections.messages.connection_invitation import (
    ConnectionInvitation,
)
from ..problem_report.message import ProblemReport
from ...storage.error import StorageNotFoundError


PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-connections/1.0'

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
        'aries_cloudagent.messaging.admin.connections'
        '.ConnectionGetList',
    CONNECTION_LIST:
        'aries_cloudagent.messaging.admin.connections'
        '.ConnectionList',
    CONNECTION_GET:
        'aries_cloudagent.messaging.admin.connections'
        '.ConnectionGet',
    CONNECTION:
        'aries_cloudagent.messaging.admin.connections'
        '.Connnection',
    CREATE_INVITATION:
        'aries_cloudagent.messaging.admin.connections'
        '.CreateInvitation',
    INVITATION_GET_LIST:
        'aries_cloudagent.messaging.admin.connections'
        '.InvitationGetList',
    INVITATION:
        'aries_cloudagent.messaging.admin.connections'
        '.Invitation',
    RECEIVE_INVITATION:
        'aries_cloudagent.messaging.admin.connections'
        '.ReceiveInvitation',
    ACCEPT_INVITATION:
        'aries_cloudagent.messaging.admin.connections'
        '.AcceptInvitation',
    ACCEPT_REQUEST:
        'aries_cloudagent.messaging.admin.connections'
        '.AcceptRequest',
    ESTABLISH_INBOUND:
        'aries_cloudagent.messaging.admin.connections'
        '.EstablishInbound',
    DELETE_CONNECTION:
        'aries_cloudagent.messaging.admin.connections'
        '.DeleteConnection',
    CONNECTION_ACK:
        'aries_cloudagent.messaging.admin.connections'
        '.ConnectionAck',
    UPDATE_CONNECTION:
        'aries_cloudagent.messaging.admin.connections'
        '.UpdateConnection',
}


ConnectionGetList, ConnectionGetListSchema = generate_model_schema(
    name='ConnectionGetList',
    handler='aries_cloudagent.messaging.admin.connections.ConnectionGetListHandler',
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
    handler='aries_cloudagent.messaging.admin.PassHandler',
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
    handler='aries_cloudagent.messaging.admin.connections.ConnectionGetHandler',
    msg_type=CONNECTION_GET,
    schema={
        'connection_id': fields.Str(required=True)
    }
)

Connection, ConnectionSchema = generate_model_schema(
    name='Connection',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=CONNECTION,
    schema={
        'connection': fields.Nested(ConnectionRecordSchema, required=True),
    }
)

InvitationGetList, InvitationGetListSchema = generate_model_schema(
    name='InvitationGetList',
    handler='aries_cloudagent.messaging.admin.connections.InvitationGetListHandler',
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
    handler='aries_cloudagent.messaging.admin.connections.CreateInvitationHandler',
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
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=INVITATION,
    schema={
        'connection_id': fields.Str(required=True),
        'invitation': fields.Str(required=True),
        'invitation_url': fields.Str(required=True)
    }
)

InvitationList, InvitationListSchema = generate_model_schema(
    name='InvitationList',
    handler='aries_cloudagent.messaging.admin.PassHandler',
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
    handler='aries_cloudagent.messaging.admin.connections.ReceiveInvitationHandler',
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
    handler='aries_cloudagent.messaging.admin.connections.AcceptInvitationHandler',
    msg_type=ACCEPT_INVITATION,
    schema={
        'connection_id': fields.Str(required=True),
        'my_endpoint': fields.Str(required=False),
        'my_label': fields.Str(required=False),
    }
)

AcceptRequest, AcceptRequestSchema = generate_model_schema(
    name='AcceptRequest',
    handler='aries_cloudagent.messaging.admin.connections.AcceptRequestHandler',
    msg_type=ACCEPT_REQUEST,
    schema={
        'connection_id': fields.Str(required=True),
        'my_endpoint': fields.Str(required=False),
    }
)

EstablishInbound, EstablishInboundSchema = generate_model_schema(
    name='EstablishInbound',
    handler='aries_cloudagent.messaging.admin.connections.EstablishInboundHandler',
    msg_type=ESTABLISH_INBOUND,
    schema={
        'connection_id': fields.Str(required=True),
        'ref_id': fields.Str(required=True),
    }
)

DeleteConnection, DeleteConnectionSchema = generate_model_schema(
    name='DeleteConnection',
    handler='aries_cloudagent.messaging.admin.connections.DeleteConnectionHandler',
    msg_type=DELETE_CONNECTION,
    schema={
        'connection_id': fields.Str(required=True),
    }
)

ConnectionAck, ConnectionAckSchema = generate_model_schema(
    name='ConnectionAck',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=CONNECTION_ACK,
    schema={}
)

UpdateConnection, UpdateConnectionSchema = generate_model_schema(
    name='UpdateConnection',
    handler='aries_cloudagent.messaging.admin.connections.UpdateConnectionHandler',
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
                'initiator': context.message.initiator,
                'invitation_key': context.message.invitation_key,
                'my_did': context.message.my_did,
                'state': context.message.state,
                'their_did': context.message.their_did,
                'their_role': context.message.their_role
            }.items())
        )
        records = await ConnectionRecord.query(context, tag_filter)
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
                'initiator': context.message.initiator,
                'invitation_key': context.message.invitation_key,
                'my_did': context.message.my_did,
                'state': 'invitation',
                'their_did': context.message.their_did,
                'their_role': context.message.their_role
            }.items())
        )
        records = await ConnectionRecord.query(context, tag_filter)
        results = []
        for connection in records:
            invitation = await connection.retrieve_invitation(context)

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

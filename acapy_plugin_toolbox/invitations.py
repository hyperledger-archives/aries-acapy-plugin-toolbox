"""Define messages for connections admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import Schema, fields

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler, BaseResponder, RequestContext
)
from aries_cloudagent.protocols.connections.v1_0.manager import ConnectionManager
from aries_cloudagent.connections.models.connection_record import (
    ConnectionRecord
)
# ProblemReport will probably be needed when a delete message is implemented
# from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError
from aries_cloudagent.messaging.valid import INDY_ISO8601_DATETIME

from .util import generate_model_schema, admin_only

PROTOCOL = (
    'https://github.com/hyperledger/aries-toolbox/'
    'tree/master/docs/admin-invitations/0.1'
)

# Message Types
INVITATION_GET_LIST = '{}/get-list'.format(PROTOCOL)
INVITATION_LIST = '{}/list'.format(PROTOCOL)
CREATE_INVITATION = '{}/create'.format(PROTOCOL)
INVITATION = '{}/invitation'.format(PROTOCOL)

# Message Type string to Message Class map
MESSAGE_TYPES = {
    CREATE_INVITATION:
        'acapy_plugin_toolbox.invitations'
        '.CreateInvitation',
    INVITATION_GET_LIST:
        'acapy_plugin_toolbox.invitations'
        '.InvitationGetList',
    INVITATION:
        'acapy_plugin_toolbox.invitations'
        '.Invitation',
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


InvitationGetList, InvitationGetListSchema = generate_model_schema(
    name='InvitationGetList',
    handler='acapy_plugin_toolbox.invitations.InvitationGetListHandler',
    msg_type=INVITATION_GET_LIST,
    schema={

    }
)

CreateInvitation, CreateInvitationSchema = generate_model_schema(
    name='CreateInvitation',
    handler='acapy_plugin_toolbox.invitations.CreateInvitationHandler',
    msg_type=CREATE_INVITATION,
    schema={
        'label': fields.Str(required=False),
        'alias': fields.Str(required=False),  # default?
        'role': fields.Str(required=False),
        'auto_accept': fields.Boolean(missing=False),
        'multi_use': fields.Boolean(missing=False),
    }
)

BaseInvitationSchema = Schema.from_dict({
    'id': fields.Str(required=True),
    'label': fields.Str(required=False),
    'alias': fields.Str(required=False),  # default?
    'role': fields.Str(required=False),
    'auto_accept': fields.Boolean(missing=False),
    'multi_use': fields.Boolean(missing=False),
    'invitation_url': fields.Str(required=True),
    'created_date': fields.Str(
        required=False, description="Time of record creation",
        **INDY_ISO8601_DATETIME
    ),
    'raw_repr': fields.Dict(required=False),
})

Invitation, InvitationSchema = generate_model_schema(
    name='Invitation',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=INVITATION,
    schema=BaseInvitationSchema
)

InvitationList, InvitationListSchema = generate_model_schema(
    name='InvitationList',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=INVITATION_LIST,
    schema={
        'results': fields.List(fields.Nested(BaseInvitationSchema))
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
            auto_accept=context.message.auto_accept,
            multi_use=bool(context.message.multi_use),
            public=False,
            alias=context.message.alias,
        )
        invite_response = Invitation(
            id=connection.connection_id,
            label=invitation.label,
            alias=connection.alias,
            role=connection.their_role,
            auto_accept=connection.accept == ConnectionRecord.ACCEPT_AUTO,
            multi_use=(
                connection.invitation_mode ==
                ConnectionRecord.INVITATION_MODE_MULTI
            ),
            invitation_url=invitation.to_url(),
            created_date=connection.created_at,
            raw_repr={
                'connection': connection.serialize(),
                'invitation': invitation.serialize(),
            }
        )
        invite_response.assign_thread_from(context.message)
        await responder.send_reply(invite_response)


class InvitationGetListHandler(BaseHandler):
    """Handler for get invitation list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get invitation list request."""

        tag_filter = dict(
            filter(lambda item: item[1] is not None, {

            }.items())
        )
        post_filter_positive = dict(filter(
            lambda item: item[1] is not None,
            {
                'state': 'invitation',
                # 'initiator': context.message.initiator,
                # 'their_role': context.message.their_role
            }.items()
        ))
        records = await ConnectionRecord.query(
            context, tag_filter, post_filter_positive
        )
        results = []
        for connection in records:
            try:
                invitation = await connection.retrieve_invitation(context)
            except StorageNotFoundError:
                continue

            invite = {
                'id': connection.connection_id,
                'label': invitation.label,
                'alias': connection.alias,
                'role': connection.their_role,
                'auto_accept': (
                    connection.accept == ConnectionRecord.ACCEPT_AUTO
                ),
                'multi_use': (
                    connection.invitation_mode ==
                    ConnectionRecord.INVITATION_MODE_MULTI
                ),
                'invitation_url': invitation.to_url(),
                'created_date': connection.created_at,
                'raw_repr': {
                    'connection': connection.serialize(),
                    'invitation': invitation.serialize(),
                }
            }

            results.append(invite)

        invitation_list = InvitationList(results=results)
        invitation_list.assign_thread_from(context.message)
        await responder.send_reply(invitation_list)

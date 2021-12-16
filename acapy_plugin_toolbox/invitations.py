"""Define messages for connections admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import Schema, fields

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.protocols.connections.v1_0.manager import ConnectionManager
from aries_cloudagent.connections.models.conn_record import ConnRecord

# ProblemReport will probably be needed when a delete message is implemented
# from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError
from aries_cloudagent.messaging.valid import INDY_ISO8601_DATETIME

from .util import generate_model_schema, admin_only

PROTOCOL = (
    "https://github.com/hyperledger/aries-toolbox/"
    "tree/master/docs/admin-invitations/0.1"
)

# Message Types
INVITATION_GET_LIST = "{}/get-list".format(PROTOCOL)
INVITATION_LIST = "{}/list".format(PROTOCOL)
CREATE_INVITATION = "{}/create".format(PROTOCOL)
INVITATION = "{}/invitation".format(PROTOCOL)

# Message Type string to Message Class map
MESSAGE_TYPES = {
    CREATE_INVITATION: "acapy_plugin_toolbox.invitations" ".CreateInvitation",
    INVITATION_GET_LIST: "acapy_plugin_toolbox.invitations" ".InvitationGetList",
    INVITATION: "acapy_plugin_toolbox.invitations" ".Invitation",
}


async def setup(session: ProfileSession, protocol_registry: ProtocolRegistry = None):
    """Setup the connections plugin."""
    if not protocol_registry:
        protocol_registry = session.inject(ProtocolRegistry)

    protocol_registry.register_message_types(MESSAGE_TYPES)


InvitationGetList, InvitationGetListSchema = generate_model_schema(
    name="InvitationGetList",
    handler="acapy_plugin_toolbox.invitations.InvitationGetListHandler",
    msg_type=INVITATION_GET_LIST,
    schema={},
)

CreateInvitation, CreateInvitationSchema = generate_model_schema(
    name="CreateInvitation",
    handler="acapy_plugin_toolbox.invitations.CreateInvitationHandler",
    msg_type=CREATE_INVITATION,
    schema={
        "label": fields.Str(required=False),
        "alias": fields.Str(required=False),  # default?
        "group": fields.Str(required=False),
        "auto_accept": fields.Boolean(missing=False),
        "multi_use": fields.Boolean(missing=False),
        "mediation_id": fields.Str(required=False),
    },
)

BaseInvitationSchema = Schema.from_dict(
    {
        "id": fields.Str(required=True),
        "label": fields.Str(required=False),
        "alias": fields.Str(required=False),  # default?
        "group": fields.Str(required=False),
        "auto_accept": fields.Boolean(missing=False),
        "multi_use": fields.Boolean(missing=False),
        "invitation_url": fields.Str(required=True),
        "created_date": fields.Str(
            required=False,
            description="Time of record creation",
            **INDY_ISO8601_DATETIME
        ),
        "mediation_id": fields.Str(required=False),
        "raw_repr": fields.Dict(required=False),
    }
)

Invitation, InvitationSchema = generate_model_schema(
    name="Invitation",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=INVITATION,
    schema=BaseInvitationSchema,
)

InvitationList, InvitationListSchema = generate_model_schema(
    name="InvitationList",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=INVITATION_LIST,
    schema={"results": fields.List(fields.Nested(BaseInvitationSchema))},
)


class CreateInvitationHandler(BaseHandler):
    """Handler for create invitation request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle create invitation request."""
        session = await context.session()
        profile = context.profile
        connection_mgr = ConnectionManager(profile)
        connection, invitation = await connection_mgr.create_invitation(
            my_label=context.message.label,
            auto_accept=context.message.auto_accept,
            multi_use=bool(context.message.multi_use),
            public=False,
            alias=context.message.alias,
            mediation_id=context.message.mediation_id,
        )
        if context.message.group:
            await connection.metadata_set(session, "group", context.message.group)
        invite_response = Invitation(
            id=connection.connection_id,
            label=invitation.label,
            alias=connection.alias,
            group=context.message.group,
            auto_accept=connection.accept == ConnRecord.ACCEPT_AUTO,
            multi_use=(connection.invitation_mode == ConnRecord.INVITATION_MODE_MULTI),
            mediation_id=context.message.mediation_id,
            invitation_url=invitation.to_url(),
            created_date=connection.created_at,
            raw_repr={
                "connection": connection.serialize(),
                "invitation": invitation.serialize(),
            },
        )
        invite_response.assign_thread_from(context.message)
        await responder.send_reply(invite_response)


class InvitationGetListHandler(BaseHandler):
    """Handler for get invitation list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get invitation list request."""

        tag_filter = dict(filter(lambda item: item[1] is not None, {}.items()))
        post_filter_positive = dict(
            filter(
                lambda item: item[1] is not None,
                {
                    "state": "invitation",
                    # 'initiator': context.message.initiator,
                }.items(),
            )
        )
        session = await context.session()
        records = await ConnRecord.query(
            session, tag_filter, post_filter_positive=post_filter_positive
        )
        results = []
        for connection in records:
            try:
                invitation = await connection.retrieve_invitation(session)
            except StorageNotFoundError:
                continue
            group = await connection.metadata_get(session, "group")

            invite = {
                "id": connection.connection_id,
                "label": invitation.label,
                "alias": connection.alias,
                "group": group,
                "auto_accept": (connection.accept == ConnRecord.ACCEPT_AUTO),
                "multi_use": (
                    connection.invitation_mode == ConnRecord.INVITATION_MODE_MULTI
                ),
                "invitation_url": invitation.to_url(),
                "created_date": connection.created_at,
                "raw_repr": {
                    "connection": connection.serialize(),
                    "invitation": invitation.serialize(),
                },
            }

            results.append(invite)

        invitation_list = InvitationList(results=results)
        invitation_list.assign_thread_from(context.message)
        await responder.send_reply(invitation_list)

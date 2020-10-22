"""BasicMessage Plugin."""
# pylint: disable=invalid-name, too-few-public-methods

from marshmallow import fields

from .util import generate_model_schema, admin_only
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler, BaseResponder, RequestContext
)
from aries_cloudagent.protocols.coordinate_mediation.v1_0.messages.mediate_request import MediationRequest
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.protocols.routing.v1_0.messages.route_update_request import RouteUpdateRequest
from aries_cloudagent.protocols.routing.v1_0.models.route_update import RouteUpdate
from aries_cloudagent.storage.error import StorageNotFoundError

ADMIN_PROTOCOL_URI = "https://github.com/hyperledger/" \
    "aries-toolbox/tree/master/docs/admin-routing/0.1"

SEND_UPDATE = f"{ADMIN_PROTOCOL_URI}/send_update"
MEDIATION_REQUEST_SEND = f"{ADMIN_PROTOCOL_URI}/mediation-request-send"
MEDIATION_REQUEST_SENT = f"{ADMIN_PROTOCOL_URI}/mediation-request-sent"
KEYLIST_UPDATE_SEND = f"{ADMIN_PROTOCOL_URI}/keylist-update-send"
KEYLIST_UPDATE_SENT = f"{ADMIN_PROTOCOL_URI}/keylist-update-sent"
ROUTES_GET = f"{ADMIN_PROTOCOL_URI}/routes-get"
ROUTES = f"{ADMIN_PROTOCOL_URI}/routes"

MESSAGE_TYPES = {
    SEND_UPDATE: 'acapy_plugin_toolbox.routing.SendUpdate',
    MEDIATION_REQUEST_SEND: 'acapy_plugin_toolbox.routing.MediationRequestSend',
    MEDIATION_REQUEST_SENT: 'acapy_plugin_toolbox.routing.MediationRequestSent',
    KEYLIST_UPDATE_SEND: 'acapy_plugin_toolbox.routing.KeylistUpdateSend',
    KEYLIST_UPDATE_SENT: 'acapy_plugin_toolbox.routing.KeylistUpdateSent',
    ROUTES_GET: 'acapy_plugin_toolbox.routing.RoutesGet',
    ROUTES: 'acapy_plugin_toolbox.routing.Routes'
}


async def setup(
        context: InjectionContext,
        protocol_registry: ProblemReport = None
):
    """Setup the routing plugin."""
    if not protocol_registry:
        protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )


SendUpdate, SendUpdateSchema = generate_model_schema(
    name='SendUpdate',
    handler='acapy_plugin_toolbox.routing.SendUpdateHandler',
    msg_type=SEND_UPDATE,
    schema={
        'connection_id': fields.Str(required=True),
        'verkey': fields.Str(required=True),
        'action': fields.Str(required=True),
    }
)


class SendUpdateHandler(BaseHandler):
    """Handler for received delete requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received delete requests."""

        update_msg = RouteUpdateRequest(updates=[
            RouteUpdate(
                recipient_key=context.message.verkey,
                action=context.message.action
            )
        ])

        # TODO make sure connection_id is valid, fail gracefully
        await responder.send(
            update_msg,
            connection_id=context.message.connection_id,
        )


MediationRequestSend, MediationRequestSendSchema = generate_model_schema(
    name='MediationRequestSend',
    handler='acapy_plugin_toolbox.routing.SendMediationRequestHandler',
    msg_type=MEDIATION_REQUEST_SEND,
    schema={
        'connection_id': fields.Str(required=True),
        'mediator_terms': fields.List(fields.Str(), required=False),
        'recipient_terms': fields.List(fields.Str(), required=False),
    }
)
MediationRequestSent, MediationRequestSentSchema = generate_model_schema(
    name="MediationRequestSent",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=MEDIATION_REQUEST_SENT,
    schema={
        'connection_id': fields.Str(required=True)
    }
)


class SendMediationRequestHandler(BaseHandler):
    """Handler for sending mediation requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        # Construct message
        mediation_request = MediationRequest(
            mediator_terms=context.message.mediator_terms,
            recipient_terms=context.message.recipient_terms,
        )

        # Verify connection exists
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

        # Send mediation request
        await responder.send(
            mediation_request,
            connection_id=connection.connection_id,
        )

        # Send notification of mediation request sent
        sent = MediationRequestSent(connection_id=connection.connection_id)
        sent.assign_thread_from(context.message)
        await responder.send_reply(sent)

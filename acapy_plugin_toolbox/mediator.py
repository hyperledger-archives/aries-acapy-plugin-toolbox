"""Define messages and handlers for mediator admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.protocols.coordinate_mediation.v1_0.manager import (
    MediationManager,
)
from aries_cloudagent.protocols.coordinate_mediation.v1_0.models.mediation_record import (
    MediationRecord,
    MediationRecordSchema,
)
from aries_cloudagent.protocols.routing.v1_0.models.route_record import (
    RouteRecord,
    RouteRecordSchema,
)
from marshmallow import fields

from .util import admin_only, generate_model_schema

PROTOCOL = (
    "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-mediator/0.1"
)

ROUTES_GET = f"{PROTOCOL}/routes-get"
ROUTES = f"{PROTOCOL}/routes"
MEDIATION_REQUESTS_GET = f"{PROTOCOL}/mediation-requests-get"
MEDIATION_REQUESTS = f"{PROTOCOL}/mediation-requests"
MEDIATION_GRANT = f"{PROTOCOL}/mediate-grant"
MEDIATION_GRANTED = f"{PROTOCOL}/mediate-granted"
MEDIATION_DENY = f"{PROTOCOL}/mediate-deny"
MEDIATION_DENIED = f"{PROTOCOL}/mediate-denied"

MESSAGE_TYPES = {
    # get all mediation records
    MEDIATION_REQUESTS_GET: "acapy_plugin_toolbox.mediator.MediationRequestsGet",
    # return type for get all mediation records for a connection
    MEDIATION_REQUESTS: "acapy_plugin_toolbox.mediator.MediationRequests",
    # get all routes used for mediation
    ROUTES_GET: "acapy_plugin_toolbox.mediator.RoutesGet",
    # return type for get all routes
    ROUTES: "acapy_plugin_toolbox.mediator.Routes",
    MEDIATION_GRANT: "acapy_plugin_toolbox.mediator.MediationGrant",
    MEDIATION_GRANTED: "acapy_plugin_toolbox.mediator.MediationGranted",
    MEDIATION_DENY: "acapy_plugin_toolbox.mediator.MediationDeny",
    MEDIATION_DENIED: "acapy_plugin_toolbox.mediator.MediationDenied",
}


async def setup(context: InjectionContext, protocol_registry: ProtocolRegistry = None):
    """Setup the admin-mediator v1_0 plugin."""
    if not protocol_registry:
        protocol_registry = context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)


MediationRequestsGet, MediationRequestsGetSchema = generate_model_schema(
    name="MediationRequestsGet",
    handler="acapy_plugin_toolbox.mediator.MediationRequestsGetHandler",
    msg_type=MEDIATION_REQUESTS_GET,
    schema={
        "state": fields.Str(required=False),
        "connection_id": fields.Str(required=False),
    },
)

MediationRequests, MediationRequestsSchema = generate_model_schema(
    name="MediationRequests",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=MEDIATION_REQUESTS,
    schema={"requests": fields.List(fields.Nested(MediationRecordSchema))},
)


class MediationRequestsGetHandler(BaseHandler):
    """Handler for received mediation requests get messages."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle mediation requests get message."""
        tag_filter = dict(
            filter(
                lambda item: item[1] is not None,
                {
                    "state": context.message.state,
                    "role": MediationRecord.ROLE_SERVER,
                    "connection_id": context.message.connection_id,
                }.items(),
            )
        )
        session = await context.session()
        records = await MediationRecord.query(session, tag_filter=tag_filter)
        response = MediationRequests(requests=records)
        response.assign_thread_from(context.message)
        await responder.send_reply(response)


MediationGrant, MediationGrantSchema = generate_model_schema(
    name="MediationGrant",
    handler="acapy_plugin_toolbox.mediator.MediationGrantHandler",
    msg_type=MEDIATION_GRANT,
    schema={"mediation_id": fields.Str(required=True)},
)


MediationGranted, MediationGrantedSchema = generate_model_schema(
    name="MediationGranted",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=MEDIATION_GRANTED,
    schema={"mediation_id": fields.Str(required=True)},
)


class MediationGrantHandler(BaseHandler):
    """
    Handler for MediationGrant messages (granting a received mediation
    request).
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle mediation grant request."""
        session = await context.session()
        manager = MediationManager(session.profile)
        record = await MediationRecord.retrieve_by_id(
            session, context.message.mediation_id
        )

        grant = await manager.grant_request(record)
        await responder.send(grant, connection_id=record.connection_id)

        granted = MediationGranted(mediation_id=record.mediation_id)
        granted.assign_thread_from(context.message)
        await responder.send_reply(granted)


MediationDeny, MediationDenySchema = generate_model_schema(
    name="MediationDeny",
    handler="acapy_plugin_toolbox.mediator.MediationDenyHandler",
    msg_type=MEDIATION_DENY,
    schema={"mediation_id": fields.Str(required=True)},
)


MediationDenied, MediationDeniedSchema = generate_model_schema(
    name="MediationDenied",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=MEDIATION_DENIED,
    schema={"mediation_id": fields.Str(required=True)},
)


class MediationDenyHandler(BaseHandler):
    """
    Handler for MediationDeny messages (denying a received mediation
    request).
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle mediation deny request."""
        session = await context.session()
        manager = MediationManager(session.profile)
        record = await MediationRecord.retrieve_by_id(
            session, context.message.mediation_id
        )

        deny = await manager.deny_request(record)
        await responder.send(deny, connection_id=record.connection_id)

        denied = MediationDenied(mediation_id=record.mediation_id)
        denied.assign_thread_from(context.message)
        await responder.send_reply(denied)


RoutesGet, RoutesGetSchema = generate_model_schema(
    name="RoutesGet",
    handler="acapy_plugin_toolbox.mediator.RoutesGetHandler",
    msg_type=ROUTES_GET,
    schema={"connection_id": fields.Str(required=False)},
)

Routes, RoutesSchema = generate_model_schema(
    name="Routes",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=ROUTES,
    schema={"routes": fields.List(fields.Nested(RouteRecordSchema))},
)


class RoutesGetHandler(BaseHandler):
    """Handler for route get request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get Route get request."""
        session = await context.session()
        tag_filter = dict(
            filter(
                lambda item: item[1] is not None,
                {
                    "connection_id": context.message.connection_id,
                    "role": MediationRecord.ROLE_SERVER,
                }.items(),
            )
        )
        records = await RouteRecord.query(session, tag_filter=tag_filter)
        response = Routes(routes=records)
        response.assign_thread_from(context.message)
        await responder.send_reply(response)

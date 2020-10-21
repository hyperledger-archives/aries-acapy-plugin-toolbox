"""Define messages and handlers for mediator admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
from marshmallow import fields

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler, BaseResponder, RequestContext
)
from aries_cloudagent.protocols.routing.v1_0.manager import RoutingManager
from aries_cloudagent.protocols.routing.v1_0.models.route_record import (
    RouteRecord, RouteRecordSchema
)
from aries_cloudagent.protocols.coordinate_mediation.v1_0.models.mediation_record import (
    MediationRecord, MediationRecordSchema
)
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport

from .util import generate_model_schema, admin_only
PROTOCOL = 'https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-mediator/0.1'

KEYLISTS_GET = '{}/keylists-get'.format(PROTOCOL)
KEYLISTS = '{}/keylists'.format(PROTOCOL)

MEDIATION_REQUESTS_GET = '{}/mediation-requests-get'.format(PROTOCOL)
MEDIATION_REQUESTS = '{}/mediation-requests'.format(PROTOCOL)

MESSAGE_TYPES = {
    MEDIATION_REQUESTS_GET:
        'acapy_plugin_toolbox.mediator.MediationRequestsGet',
    MEDIATION_REQUESTS:
        'acapy_plugin_toolbox.mediator.MediationRequests',
    KEYLISTS:
        'acapy_plugin_toolbox.mediator.Keylists',
    KEYLISTS_GET:
        'acapy_plugin_toolbox.mediator.KeylistsGet',
}


async def setup(
        context: InjectionContext,
        protocol_registry: ProblemReport = None
):
    """Setup the admin-mediator v1_0 plugin."""
    if not protocol_registry:
        protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )

MediationRequestsGet, MediationRequestsGetSchema = generate_model_schema(
    name='MediationRequestsGet',
    handler='acapy_plugin_toolbox.mediator.MediationRequestsGetHandler',
    msg_type=MEDIATION_REQUESTS_GET,
    schema={
        'state': fields.Str(required=True),
        'connection_id': fields.Str(required=False)
    }
)

MediationRequests, MediationRequestsSchema = generate_model_schema(
    name='MediationRequests',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=MEDIATION_REQUESTS,
    schema={
        'requests': fields.List(fields.Nested(MediationRecordSchema))
    }
)


class MediationRequestsGetHandler(BaseHandler):
    """Handler for received mediation requests get messages."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle mediation requests get message."""
        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                'state': context.message.state,
                'connection_id': context.message.connection_id
            })
        )
        records = MediationRecord.query(context, tag_filter=tag_filter)
        response = MediationRequests(requests=records)
        response.assign_thread_from(context.message)
        await responder.send_reply(response)


KeylistsGet, KeylistsGetSchema = generate_model_schema(
    name='KeylistsGet',
    handler='acapy_plugin_toolbox.mediator.KeyListsGetHandler',
    msg_type=KEYLISTS_GET,
    schema={
        'connection_id': fields.Str(required=False)
    }
)

KeyLists, KeyListsSchema = generate_model_schema(
    name='KeyLists',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=KEYLISTS,
    schema={
        'keylists': fields.List(fields.Nested(RouteRecordSchema))
    }
)


class KeyListsGetHandler(BaseHandler):
    """Handler for keylist get request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get Keylist get request."""
        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                'connection_id': context.message.connection_id
            })
        )
        records = RouteRecord.query(context, tag_filter=tag_filter)
        response = KeyLists(requests=records)
        response.assign_thread_from(context.message)
        await responder.send_reply(response)

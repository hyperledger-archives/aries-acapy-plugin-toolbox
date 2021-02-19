"""Define messages for credential holder admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

import re
from typing import Sequence

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.event_bus import Event, EventBus
from aries_cloudagent.core.profile import Profile
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.indy.holder import IndyHolder
from aries_cloudagent.messaging.agent_message import AgentMessage
from aries_cloudagent.messaging.base_handler import (
    BaseHandler, BaseResponder, RequestContext
)
from aries_cloudagent.messaging.models.base import BaseModel
from aries_cloudagent.protocols.issue_credential.v1_0.messages.inner.credential_preview import (
    CredAttrSpec
)
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import \
    V10CredentialExchange as CredExRecord
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import \
    V10CredentialExchangeSchema as CredExRecordSchema
from aries_cloudagent.protocols.issue_credential.v1_0.routes import (
    V10CredentialProposalRequestMandSchema
)
from aries_cloudagent.protocols.issue_credential.v1_0.manager import CredentialManager
from aries_cloudagent.protocols.issue_credential.v1_0.messages.credential_proposal import CredentialProposal
from aries_cloudagent.protocols.present_proof import v1_0 as proof
from aries_cloudagent.protocols.present_proof.v1_0.messages.inner.presentation_preview import (
    PresentationPreview
)
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange, V10PresentationExchangeSchema
)
from aries_cloudagent.protocols.present_proof.v1_0.routes import (
    V10PresentationProposalRequestSchema
)
from aries_cloudagent.protocols.problem_report.v1_0.message import (
    ProblemReport
)
from aries_cloudagent.storage.error import StorageNotFoundError
from marshmallow import fields

from ..decorators.pagination import Page, Paginate
from ..util import (
    ExceptionReporter, InvalidConnection, admin_only, expand_message_class,
    expand_model_class, get_connection, send_to_admins
)

PASS = 'acapy_plugin_toolbox.util.PassHandler'
PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1'
PACKAGE = 'acapy_plugin_toolbox.holder.v0_1'


@expand_model_class
class CredentialRepresentation(BaseModel):
    """Representation of Credentials in messages."""
    class Fields:
        """Fields for Credential Representation."""
        issuer_did = fields.Str()
        isser_connection_id = fields.Str()
        name = fields.Str()
        comment = fields.Str()
        received_at = fields.DateTime(format="iso")
        attributes = fields.List(fields.Nested(CredAttrSpec))
        metadata = fields.Dict()
        raw_repr = fields.Dict()

    def __init__(
        self,
        *,
        issuer_did: str = None,
        issuer_connection_id: str = None,
        name: str = None,
        comment: str = None,
        received_at: str = None,
        attributes: Sequence[CredAttrSpec] = None,
        metadata: dict = None,
        raw_repr: dict = None
    ):
        """Initialize model."""
        self.issuer_did = issuer_did
        self.issuer_connection_id = issuer_connection_id
        self.name = name
        self.comment = comment
        self.received_at = received_at
        self.attributes = attributes
        self.metadata = metadata
        self.raw_repr = raw_repr


@expand_message_class
class CredGetList(AgentMessage):
    """Credential list retrieval message."""
    protocol = PROTOCOL
    message_type = "credentials-get-list"
    handler = f"{PACKAGE}.CredGetListHandler"

    class Fields:
        """Credential get list fields."""
        paginate = fields.Nested(
            Paginate.Schema,
            required=False,
            data_key="~paginate",
            missing=Paginate(limit=10, offset=0)
        )

    def __init__(self, connection_id: str = None, paginate: Paginate = None, **kwargs):
        super().__init__(**kwargs)
        self.connection_id = connection_id
        self.paginate = paginate


@expand_message_class
class CredList(AgentMessage):
    """Credential list message."""
    protocol = PROTOCOL
    message_type = "credentials-list"
    handler = PASS

    class Fields:
        """Fields of credential list message."""
        results = fields.List(fields.Dict())
        page = fields.Nested(Page.Schema, required=False, data_key="~page")

    def __init__(
        self,
        results: Sequence[dict],
        page: Page = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.results = results
        self.page = page


@expand_message_class
class SendCredProposal(AgentMessage):
    """Send Credential Proposal Message."""
    protocol = PROTOCOL
    message_type = "send-credential-proposal"
    handler = f"{PACKAGE}.SendCredProposalHandler"
    fields_from = V10CredentialProposalRequestMandSchema


@expand_message_class
class CredExchange(AgentMessage):
    """Credential exchange message."""
    protocol = PROTOCOL
    message_type = "credential-exchange"
    handler = PASS
    fields_from = CredExRecordSchema


@expand_message_class
class CredOfferRecv(AgentMessage):
    """Credential offer received message."""
    protocol = PROTOCOL
    message_type = "credential-offer-received"
    handler = PASS
    fields_from = CredExRecordSchema


@expand_message_class
class PresGetList(AgentMessage):
    """Presentation get list message."""
    protocol = PROTOCOL
    message_type = 'presentations-get-list'
    handler = f"{PACKAGE}.PresGetListHandler"

    class Fields:
        """Message fields."""
        connection_id = fields.Str(required=False)
        verified = fields.Str(required=False)
        paginate = fields.Nested(
            Paginate.Schema,
            required=False,
            data_key="~paginate",
            missing=Paginate(limit=10, offset=0)
        )

    def __init__(
        self,
        connection_id: str = None,
        verified: str = None,
        paginate: Paginate = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.connection_id = connection_id
        self.verified = verified
        self.paginate = paginate


@expand_message_class
class PresList(AgentMessage):
    """Presentation get list response message."""
    protocol = PROTOCOL
    message_type = 'presentations-list'
    handler = PASS

    class Fields:
        """Fields for presentation list message."""
        results = fields.List(fields.Dict())
        page = fields.Nested(Page.Schema, required=False, data_key="~page")

    def __init__(self, results, page: Page = None, **kwargs):
        super().__init__(**kwargs)
        self.results = results
        self.page = page


@expand_message_class
class SendPresProposal(AgentMessage):
    """Presentation proposal message."""
    protocol = PROTOCOL
    message_type = 'send-presentation-proposal'
    handler = f"{PACKAGE}.SendPresProposalHandler"
    fields_from = V10PresentationProposalRequestSchema

    def __init__(
        self,
        *,
        connection_id: str = None,
        comment: str = None,
        presentation_proposal: PresentationPreview = None,
        auto_present: bool = None,
        trace: bool = None
    ):
        self.connection_id = connection_id
        self.comment = comment
        self.presentation_proposal = presentation_proposal
        self.auto_present = auto_present
        self.trace = trace


@expand_message_class
class PresExchange(AgentMessage):
    """Presentation Exchange message."""
    protocol = PROTOCOL
    message_type = "presentation-exchange"
    handler = PASS
    fields_from = V10PresentationExchangeSchema


MESSAGE_TYPES = {
    msg_class.Meta.message_type: '{}.{}'.format(PACKAGE, msg_class.__name__)
    for msg_class in [
        PresGetList, PresList, SendPresProposal, PresExchange,
        CredGetList, CredList, SendCredProposal, CredExchange,
        CredOfferRecv
    ]
}


async def setup(
        context: InjectionContext,
        protocol_registry: ProblemReport = None
):
    """Setup the holder plugin."""
    if not protocol_registry:
        protocol_registry = context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )
    bus: EventBus = context.inject(EventBus)
    bus.subscribe(
        re.compile(CredExRecord.WEBHOOK_TOPIC + ".*"),
        issue_credential_event_handler
    )


async def issue_credential_event_handler(profile: Profile, event: Event):
    """Handle issue credential events."""
    record: CredExRecord = CredExRecord.deserialize(event.payload)
    if record.state == CredExRecord.STATE_OFFER_RECEIVED:
        offer_recv = CredOfferRecv(**record.serialize())
        responder = profile.inject(BaseResponder)
        async with profile.session() as session:
            await send_to_admins(
                session,
                offer_recv,
                responder
            )


class SendCredProposalHandler(BaseHandler):
    """Handler for received send proposal request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send proposal request."""
        connection_id = str(context.message.connection_id)
        credential_definition_id = context.message.credential_definition_id
        comment = context.message.comment

        credential_manager = CredentialManager(context.profile)

        session = await context.session()
        try:
            conn_record = await ConnRecord.retrieve_by_id(
                session,
                connection_id
            )
        except StorageNotFoundError:
            report = ProblemReport(
                explain_ltxt='Connection not found.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        if not conn_record.is_ready:
            report = ProblemReport(
                explain_ltxt='Connection invalid.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        credential_exchange_record = await credential_manager.create_proposal(
            connection_id,
            comment=comment,
            credential_preview=context.message.credential_proposal,
            cred_def_id=credential_definition_id
        )

        await responder.send(
            CredentialProposal(
                comment=context.message.comment,
                credential_proposal=context.message.credential_proposal,
                cred_def_id=context.message.credential_definition_id
            ),
            connection_id=connection_id
        )
        cred_exchange = CredExchange(**credential_exchange_record.serialize())
        cred_exchange.assign_thread_from(context.message)
        await responder.send_reply(cred_exchange)


class SendPresProposalHandler(BaseHandler):
    """Handler for received send presentation proposal request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send presentation proposal request."""
        session = await context.session()
        connection_id = str(context.message.connection_id)
        async with ExceptionReporter(responder, InvalidConnection, context.message):
            await get_connection(session, connection_id)

        comment = context.message.comment
        # Aries#0037 calls it a proposal in the proposal struct but it's of type preview
        presentation_proposal = proof.messages.presentation_proposal.PresentationProposal(
            comment=comment,
            presentation_proposal=context.message.presentation_proposal
        )
        auto_present = (
            context.message.auto_present or
            context.settings.get("debug.auto_respond_presentation_request")
        )

        presentation_manager = proof.manager.PresentationManager(session)

        presentation_exchange_record = (
            await presentation_manager.create_exchange_for_proposal(
                connection_id=connection_id,
                presentation_proposal_message=presentation_proposal,
                auto_present=auto_present
            )
        )
        await responder.send(presentation_proposal, connection_id=connection_id)

        pres_exchange = PresExchange(**presentation_exchange_record.serialize())
        pres_exchange.assign_thread_from(context.message)
        await responder.send_reply(pres_exchange)


class CredGetListHandler(BaseHandler):
    """Handler for received get cred list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""
        session = await context.session()
        holder: IndyHolder = session.inject(IndyHolder)

        paginate: Paginate = context.message.paginate
        credentials = await holder.get_credentials(paginate.offset, paginate.limit, {})
        page = Page(len(credentials), paginate.offset)

        cred_list = CredList(results=credentials, page=page)
        await responder.send_reply(cred_list)


class PresGetListHandler(BaseHandler):
    """Handler for received get cred list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""

        session = await context.session()
        paginate: Paginate = context.message.paginate

        post_filter_positive = dict(
            filter(lambda item: item[1] is not None, {
                # 'state': V10PresentialExchange.STATE_CREDENTIAL_RECEIVED,
                'role': V10PresentationExchange.ROLE_PROVER,
                'connection_id': context.message.connection_id,
                'verified': context.message.verified,
            }.items())
        )
        records = await V10PresentationExchange.query(
            session, {}, post_filter_positive=post_filter_positive
        )
        cred_list = PresList(*paginate.apply(records))
        await responder.send_reply(cred_list)

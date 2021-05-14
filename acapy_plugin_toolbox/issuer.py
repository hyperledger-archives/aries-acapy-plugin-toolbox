"""Define messages for credential issuer admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.indy.util import generate_pr_nonce
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.messaging.credential_definitions.util import CRED_DEF_TAGS
from aries_cloudagent.messaging.decorators.attach_decorator import AttachDecorator
from aries_cloudagent.protocols.issue_credential.v1_0.manager import CredentialManager
from aries_cloudagent.protocols.issue_credential.v1_0.messages.credential_proposal import (  # noqa: E501
    CredentialProposal,
)
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange,
    V10CredentialExchangeSchema,
)
from aries_cloudagent.protocols.issue_credential.v1_0.routes import (
    V10CredentialExchangeListResultSchema,
    V10CredentialProposalRequestMandSchema,
)
from aries_cloudagent.protocols.present_proof.v1_0.manager import PresentationManager
from aries_cloudagent.protocols.present_proof.v1_0.message_types import (
    ATTACH_DECO_IDS,
    PRESENTATION_REQUEST,
)
from aries_cloudagent.protocols.present_proof.v1_0.messages.presentation_request import (
    PresentationRequest,
)
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange,
    V10PresentationExchangeSchema,
)
from aries_cloudagent.protocols.present_proof.v1_0.routes import (
    V10PresentationExchangeListSchema,
    V10PresentationSendRequestRequestSchema,
)
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError
from marshmallow import fields

from .util import admin_only, generate_model_schema

PROTOCOL = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-issuer/0.1"

SEND_CREDENTIAL = "{}/send-credential".format(PROTOCOL)
REQUEST_PRESENTATION = "{}/request-presentation".format(PROTOCOL)
ISSUER_CRED_EXCHANGE = "{}/credential-exchange".format(PROTOCOL)
ISSUER_PRES_EXCHANGE = "{}/presentation-exchange".format(PROTOCOL)
CREDENTIALS_GET_LIST = "{}/credentials-get-list".format(PROTOCOL)
CREDENTIALS_LIST = "{}/credentials-list".format(PROTOCOL)
PRESENTATIONS_GET_LIST = "{}/presentations-get-list".format(PROTOCOL)
PRESENTATIONS_LIST = "{}/presentations-list".format(PROTOCOL)

MESSAGE_TYPES = {
    SEND_CREDENTIAL: "acapy_plugin_toolbox.issuer.SendCred",
    REQUEST_PRESENTATION: "acapy_plugin_toolbox.issuer.RequestPres",
    CREDENTIALS_GET_LIST: "acapy_plugin_toolbox.issuer.CredGetList",
    CREDENTIALS_LIST: "acapy_plugin_toolbox.issuer.CredList",
    PRESENTATIONS_GET_LIST: "acapy_plugin_toolbox.issuer.PresGetList",
    PRESENTATIONS_LIST: "acapy_plugin_toolbox.issuer.PresList",
}


async def setup(session: ProfileSession, protocol_registry: ProblemReport = None):
    """Setup the issuer plugin."""
    if not protocol_registry:
        protocol_registry = session.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)


SendCred, SendCredSchema = generate_model_schema(
    name="SendCred",
    handler="acapy_plugin_toolbox.issuer.SendCredHandler",
    msg_type=SEND_CREDENTIAL,
    schema=V10CredentialProposalRequestMandSchema,
)
IssuerCredExchange, IssuerCredExchangeSchema = generate_model_schema(
    name="IssuerCredExchange",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=ISSUER_CRED_EXCHANGE,
    schema=V10CredentialExchangeSchema,
)


class SendCredHandler(BaseHandler):
    """Handler for received send request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send request."""
        comment = context.message.comment
        connection_id = str(context.message.connection_id)
        preview_spec = context.message.credential_proposal

        session = await context.session()
        try:
            conn_record = await ConnRecord.retrieve_by_id(session, connection_id)
        except StorageNotFoundError:
            report = ProblemReport(
                explain_ltxt="Connection not found.", who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        if not conn_record.is_ready:
            report = ProblemReport(
                explain_ltxt="Connection invalid.", who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        credential_proposal = CredentialProposal(
            comment=comment,
            credential_proposal=preview_spec,
            **{
                t: getattr(context.message, t)
                for t in CRED_DEF_TAGS
                if hasattr(context.message, t)
            },
        )

        credential_manager = CredentialManager(context.profile)

        (
            cred_exchange_record,
            cred_offer_message,
        ) = await credential_manager.prepare_send(
            connection_id, credential_proposal=credential_proposal
        )

        await responder.send(
            cred_offer_message, connection_id=cred_exchange_record.connection_id
        )
        cred_exchange = IssuerCredExchange(**cred_exchange_record.serialize())
        cred_exchange.assign_thread_from(context.message)
        await responder.send_reply(cred_exchange)


RequestPres, RequestPresSchema = generate_model_schema(
    name="RequestPres",
    handler="acapy_plugin_toolbox.issuer.RequestPresHandler",
    msg_type=REQUEST_PRESENTATION,
    schema=V10PresentationSendRequestRequestSchema,
)
IssuerPresExchange, IssuerPresExchangeSchema = generate_model_schema(
    name="IssuerPresExchange",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=ISSUER_PRES_EXCHANGE,
    schema=V10PresentationExchangeSchema,
)


class RequestPresHandler(BaseHandler):
    """Handler for received presentation request request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received presentation request request."""

        connection_id = str(context.message.connection_id)
        session = await context.session()
        try:
            conn_record = await ConnRecord.retrieve_by_id(session, connection_id)
        except StorageNotFoundError:
            report = ProblemReport(
                explain_ltxt="Connection not found.", who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        if not conn_record.is_ready:
            report = ProblemReport(
                explain_ltxt="Connection invalid.", who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        comment = context.message.comment

        indy_proof_request = context.message.proof_request
        if not indy_proof_request.get("nonce"):
            indy_proof_request["nonce"] = await generate_pr_nonce()

        presentation_request_message = PresentationRequest(
            comment=comment,
            request_presentations_attach=[
                AttachDecorator.data_base64(
                    mapping=indy_proof_request,
                    ident=ATTACH_DECO_IDS[PRESENTATION_REQUEST],
                )
            ],
        )

        presentation_manager = PresentationManager(context.profile)

        presentation_exchange_record = (
            await presentation_manager.create_exchange_for_request(
                connection_id=connection_id,
                presentation_request_message=presentation_request_message,
            )
        )

        await responder.send(presentation_request_message, connection_id=connection_id)

        pres_exchange = IssuerPresExchange(**presentation_exchange_record.serialize())
        pres_exchange.assign_thread_from(context.message)
        await responder.send_reply(pres_exchange)


CredGetList, CredGetListSchema = generate_model_schema(
    name="CredGetList",
    handler="acapy_plugin_toolbox.issuer.CredGetListHandler",
    msg_type=CREDENTIALS_GET_LIST,
    schema={
        "connection_id": fields.Str(required=False),
        "cred_def_id": fields.Str(required=False),
        "schema_id": fields.Str(required=False),
    },
)

CredList, CredListSchema = generate_model_schema(
    name="CredList",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=CREDENTIALS_LIST,
    schema=V10CredentialExchangeListResultSchema,
)


class CredGetListHandler(BaseHandler):
    """Handler for received get cred list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""

        post_filter_positive = dict(
            filter(
                lambda item: item[1] is not None,
                {
                    # 'state': V10CredentialExchange.STATE_ISSUED,
                    "role": V10CredentialExchange.ROLE_ISSUER,
                    "connection_id": context.message.connection_id,
                    "credential_definition_id": context.message.cred_def_id,
                    "schema_id": context.message.schema_id,
                }.items(),
            )
        )
        session = await context.session()
        records = await V10CredentialExchange.query(
            session, {}, post_filter_positive=post_filter_positive
        )
        cred_list = CredList(results=records)
        await responder.send_reply(cred_list)


PresGetList, PresGetListSchema = generate_model_schema(
    name="PresGetList",
    handler="acapy_plugin_toolbox.issuer.PresGetListHandler",
    msg_type=PRESENTATIONS_GET_LIST,
    schema={
        "connection_id": fields.Str(required=False),
        "verified": fields.Str(required=False),
    },
)

PresList, PresListSchema = generate_model_schema(
    name="PresList",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=PRESENTATIONS_LIST,
    schema=V10PresentationExchangeListSchema
    # schema={
    #     'results': fields.List(fields.Dict())
    # }
)


class PresGetListHandler(BaseHandler):
    """Handler for received get cred list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""

        post_filter_positive = dict(
            filter(
                lambda item: item[1] is not None,
                {
                    # 'state': V10PresentialExchange.STATE_CREDENTIAL_RECEIVED,
                    "role": V10PresentationExchange.ROLE_VERIFIER,
                    "connection_id": context.message.connection_id,
                    "verified": context.message.verified,
                }.items(),
            )
        )
        session = await context.session()
        records = await V10PresentationExchange.query(
            session, {}, post_filter_positive=post_filter_positive
        )
        cred_list = PresList(results=records)
        await responder.send_reply(cred_list)

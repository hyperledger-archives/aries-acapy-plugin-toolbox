"""Define messages for credential holder admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import fields

from . import generate_model_schema, admin_only
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ..issue_credential.v1_0.routes import (
    V10CredentialExchangeListResultSchema,
    V10CredentialProposalRequestSchema
)
from ..issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange,
    V10CredentialExchangeSchema
)
from ..issue_credential.v1_0.messages.credential_proposal import (
    CredentialProposal,
)
from ..issue_credential.v1_0.manager import CredentialManager

from ..present_proof.v1_0.routes import (
    V10PresentationExchangeListSchema,
    V10PresentationProposalRequestSchema
)
from ..present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange,
    V10PresentationExchangeSchema
)
from ..present_proof.v1_0.messages.presentation_proposal import (
    PresentationProposal,
)
from ..present_proof.v1_0.manager import PresentationManager

from ..connections.models.connection_record import ConnectionRecord
from ...storage.error import StorageNotFoundError
from ..problem_report.message import ProblemReport
# from ...holder.base import BaseHolder

PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/1.0'

SEND_CRED_PROPOSAL = '{}/send-credential-proposal'.format(PROTOCOL)
CRED_EXCHANGE = '{}/credential-exchange'.format(PROTOCOL)
SEND_PRES_PROPOSAL = '{}/send-presentation-proposal'.format(PROTOCOL)
PRES_EXCHANGE = '{}/presentation-exchange'.format(PROTOCOL)
CREDENTIALS_GET_LIST = '{}/credentials-get-list'.format(PROTOCOL)
CREDENTIALS_LIST = '{}/credentials-list'.format(PROTOCOL)
PRESENTATIONS_GET_LIST = '{}/presentations-get-list'.format(PROTOCOL)
PRESENTATIONS_LIST = '{}/presentations-list'.format(PROTOCOL)

MESSAGE_TYPES = {
    SEND_CRED_PROPOSAL:
        'aries_cloudagent.messaging.admin.holder.SendCredProposal',
    SEND_PRES_PROPOSAL:
        'aries_cloudagent.messaging.admin.holder.SendPresProposal',
    CREDENTIALS_GET_LIST:
        'aries_cloudagent.messaging.admin.holder.CredGetList',
    CREDENTIALS_LIST:
        'aries_cloudagent.messaging.admin.holder.CredList',
    PRESENTATIONS_GET_LIST:
        'aries_cloudagent.messaging.admin.holder.PresGetList',
    PRESENTATIONS_LIST:
        'aries_cloudagent.messaging.admin.holder.PresList',
}

SendCredProposal, SendCredProposalSchema = generate_model_schema(
    name='SendCredProposal',
    handler='aries_cloudagent.messaging.admin.holder.SendCredProposalHandler',
    msg_type=SEND_CRED_PROPOSAL,
    schema=V10CredentialProposalRequestSchema
)

CredExchange, CredExchangeSchema = generate_model_schema(
    name='CredExchange',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=CRED_EXCHANGE,
    schema=V10CredentialExchangeSchema
)


class SendCredProposalHandler(BaseHandler):
    """Handler for received send proposal request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send proposal request."""
        connection_id = str(context.message.connection_id)
        credential_definition_id = context.message.credential_definition_id
        comment = context.message.comment

        credential_manager = CredentialManager(context)

        try:
            connection_record = await ConnectionRecord.retrieve_by_id(
                context,
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

        if not connection_record.is_ready:
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
            credential_definition_id=credential_definition_id
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


SendPresProposal, SendPresProposalSchema = generate_model_schema(
    name='SendPresProposal',
    handler='aries_cloudagent.messaging.admin.holder.SendPresProposalHandler',
    msg_type=SEND_PRES_PROPOSAL,
    schema=V10PresentationProposalRequestSchema
)

PresExchange, PresExchangeSchema = generate_model_schema(
    name='PresExchange',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=PRES_EXCHANGE,
    schema=V10PresentationExchangeSchema
)


class SendPresProposalHandler(BaseHandler):
    """Handler for received send presentation proposal request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send presentation proposal request."""

        connection_id = str(context.message.connection_id)
        try:
            connection_record = await ConnectionRecord.retrieve_by_id(
                context,
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

        if not connection_record.is_ready:
            report = ProblemReport(
                explain_ltxt='Connection invalid.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        comment = context.message.comment
        # Aries#0037 calls it a proposal in the proposal struct but it's of type preview
        presentation_proposal = PresentationProposal(
            comment=comment,
            presentation_proposal=context.message.presentation_proposal
        )
        auto_present = (
            context.message.auto_present or
            context.settings.get("debug.auto_respond_presentation_request")
        )

        presentation_manager = PresentationManager(context)

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


CredGetList, CredGetListSchema = generate_model_schema(
    name='CredGetList',
    handler='aries_cloudagent.messaging.admin.holder.CredGetListHandler',
    msg_type=CREDENTIALS_GET_LIST,
    schema={
        'connection_id': fields.Str(required=False),
        'credential_definition_id': fields.Str(required=False),
        'schema_id': fields.Str(required=False)
    }
)

CredList, CredListSchema = generate_model_schema(
    name='CredList',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=CREDENTIALS_LIST,
    schema=V10CredentialExchangeListResultSchema
    # schema={
    #     'results': fields.List(fields.Dict())
    # }
)


class CredGetListHandler(BaseHandler):
    """Handler for received get cred list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""

        # holder: BaseHolder = await context.inject(BaseHolder)
        # credentials = await holder.get_credentials(0, 100, {})
        # cred_list = CredList(results=credentials)
        # await responder.send_reply(cred_list)

        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                # 'state': V10CredentialExchange.STATE_CREDENTIAL_RECEIVED,
                'role': V10CredentialExchange.ROLE_HOLDER,
                'connection_id': context.message.connection_id,
                'credential_definition_id': context.message.credential_definition_id,
                'schema_id': context.message.schema_id
            }.items())
        )
        records = await V10CredentialExchange.query(context, tag_filter)
        cred_list = CredList(results=records)
        await responder.send_reply(cred_list)


PresGetList, PresGetListSchema = generate_model_schema(
    name='PresGetList',
    handler='aries_cloudagent.messaging.admin.holder.PresGetListHandler',
    msg_type=PRESENTATIONS_GET_LIST,
    schema={
        'connection_id': fields.Str(required=False),
        'verified': fields.Str(required=False),
    }
)

PresList, PresListSchema = generate_model_schema(
    name='PresList',
    handler='aries_cloudagent.messaging.admin.PassHandler',
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

        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                # 'state': V10PresentialExchange.STATE_CREDENTIAL_RECEIVED,
                'role': V10PresentationExchange.ROLE_PROVER,
                'connection_id': context.message.connection_id,
                'verified': context.message.verified,
            }.items())
        )
        records = await V10PresentationExchange.query(context, tag_filter)
        cred_list = PresList(results=records)
        await responder.send_reply(cred_list)

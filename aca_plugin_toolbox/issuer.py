"""Define messages for credential issuer admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
import asyncio

from uuid import uuid4

from marshmallow import fields

from . import generate_model_schema, admin_only
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ..decorators.attach_decorator import AttachDecorator
from ..issue_credential.v1_0.routes import (
    V10CredentialExchangeListResultSchema,
    V10CredentialProposalRequestSchema
)
from ..issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange,
    V10CredentialExchangeSchema,
)
from ..issue_credential.v1_0.messages.credential_proposal import (
    CredentialProposal
)
from ..present_proof.v1_0.routes import (
    V10PresentationExchangeListSchema,
    V10PresentationRequestRequestSchema
)
from ..present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange,
    V10PresentationExchangeSchema,
)
from ..present_proof.v1_0.messages.presentation_request import PresentationRequest
from ..present_proof.v1_0.manager import PresentationManager
from ..issue_credential.v1_0.manager import CredentialManager
from ..connections.models.connection_record import ConnectionRecord
from ...storage.error import StorageNotFoundError
from ..problem_report.message import ProblemReport

PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-issuer/1.0'

SEND_CREDENTIAL = '{}/send-credential'.format(PROTOCOL)
REQUEST_PRESENTATION = '{}/request-presentation'.format(PROTOCOL)
ISSUER_CRED_EXCHANGE = '{}/credential-exchange'.format(PROTOCOL)
ISSUER_PRES_EXCHANGE = '{}/presentation-exchange'.format(PROTOCOL)
CREDENTIALS_GET_LIST = '{}/credentials-get-list'.format(PROTOCOL)
CREDENTIALS_LIST = '{}/credentials-list'.format(PROTOCOL)
PRESENTATIONS_GET_LIST = '{}/presentations-get-list'.format(PROTOCOL)
PRESENTATIONS_LIST = '{}/presentations-list'.format(PROTOCOL)

MESSAGE_TYPES = {
    SEND_CREDENTIAL:
        'aries_cloudagent.messaging.admin.issuer.SendCred',
    REQUEST_PRESENTATION:
        'aries_cloudagent.messaging.admin.issuer.RequestPres',
    CREDENTIALS_GET_LIST:
        'aries_cloudagent.messaging.admin.issuer.CredGetList',
    CREDENTIALS_LIST:
        'aries_cloudagent.messaging.admin.issuer.CredList',
    PRESENTATIONS_GET_LIST:
        'aries_cloudagent.messaging.admin.issuer.PresGetList',
    PRESENTATIONS_LIST:
        'aries_cloudagent.messaging.admin.issuer.PresList',
}

SendCred, SendCredSchema = generate_model_schema(
    name='SendCred',
    handler='aries_cloudagent.messaging.admin.issuer.SendCredHandler',
    msg_type=SEND_CREDENTIAL,
    schema=V10CredentialProposalRequestSchema
)
IssuerCredExchange, IssuerCredExchangeSchema = generate_model_schema(
    name='IssuerCredExchange',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=ISSUER_CRED_EXCHANGE,
    schema=V10CredentialExchangeSchema
)


class SendCredHandler(BaseHandler):
    """Handler for received send request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send request."""
        connection_id = str(context.message.connection_id)
        credential_definition_id = context.message.credential_definition_id
        comment = context.message.comment
        credential_proposal = CredentialProposal(
            comment=comment,
            credential_proposal=context.message.credential_proposal,
            cred_def_id=credential_definition_id,
        )

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

        credential_exchange_record = await credential_manager.prepare_send(
            credential_definition_id,
            connection_id,
            credential_proposal=credential_proposal
        )
        asyncio.ensure_future(
            credential_manager.perform_send(
                credential_exchange_record,
                responder.send
            )
        )
        cred_exchange = IssuerCredExchange(**credential_exchange_record.serialize())
        cred_exchange.assign_thread_from(context.message)
        await responder.send_reply(cred_exchange)


RequestPres, RequestPresSchema = generate_model_schema(
    name='RequestPres',
    handler='aries_cloudagent.messaging.admin.issuer.RequestPresHandler',
    msg_type=REQUEST_PRESENTATION,
    schema=V10PresentationRequestRequestSchema,
)
IssuerPresExchange, IssuerPresExchangeSchema = generate_model_schema(
    name='IssuerPresExchange',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=ISSUER_PRES_EXCHANGE,
    schema=V10PresentationExchangeSchema
)


class RequestPresHandler(BaseHandler):
    """Handler for received presentation request request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received presentation request request."""

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

        indy_proof_request = context.message.proof_request
        if not indy_proof_request.get('nonce'):
            indy_proof_request['nonce'] = str(uuid4().int)

        presentation_request_message = PresentationRequest(
            comment=comment,
            request_presentations_attach=[
                AttachDecorator.from_indy_dict(indy_proof_request)
            ]
        )

        presentation_manager = PresentationManager(context)

        presentation_exchange_record = (
            await presentation_manager.create_exchange_for_request(
                connection_id=connection_id,
                presentation_request_message=presentation_request_message
            )
        )

        await responder.send(
            presentation_request_message,
            connection_id=connection_id
        )

        pres_exchange = IssuerPresExchange(**presentation_exchange_record.serialize())
        pres_exchange.assign_thread_from(context.message)
        await responder.send_reply(pres_exchange)


CredGetList, CredGetListSchema = generate_model_schema(
    name='CredGetList',
    handler='aries_cloudagent.messaging.admin.issuer.CredGetListHandler',
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
)


class CredGetListHandler(BaseHandler):
    """Handler for received get cred list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""

        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                # 'state': V10CredentialExchange.STATE_ISSUED,
                'role': V10CredentialExchange.ROLE_ISSUER,
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
    handler='aries_cloudagent.messaging.admin.issuer.PresGetListHandler',
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
                'role': V10PresentationExchange.ROLE_VERIFIER,
                'connection_id': context.message.connection_id,
                'verified': context.message.verified,
            }.items())
        )
        records = await V10PresentationExchange.query(context, tag_filter)
        cred_list = PresList(results=records)
        await responder.send_reply(cred_list)

from typing import cast

from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.protocols.issue_credential import v1_0 as issue_credential
from aries_cloudagent.protocols.issue_credential.v1_0.manager import CredentialManager
from aries_cloudagent.protocols.issue_credential.v1_0.routes import (
    V10CredentialProposalRequestMandSchema as CredentialProposalRequestSchema,
)
from aries_cloudagent.storage.error import StorageNotFoundError

from .... import ProblemReport
from ....util import admin_only, expand_message_class, log_handling, with_generic_init
from .base import AdminHolderMessage
from .cred_exchange import CredExchange


@with_generic_init
@expand_message_class
class SendCredProposal(AdminHolderMessage):
    """Send Credential Proposal Message."""

    message_type = "send-credential-proposal"
    fields_from = CredentialProposalRequestSchema

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send proposal request."""
        connection_id = str(context.message.connection_id)
        credential_definition_id = context.message.cred_def_id
        comment = context.message.comment

        credential_manager = CredentialManager(context.profile)

        session = await context.session()
        try:
            conn_record = await ConnRecord.retrieve_by_id(session, connection_id)
            conn_record = cast(ConnRecord, conn_record)
        except StorageNotFoundError:
            report = ProblemReport(
                description={"en": "Connection not found."}, who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        if not conn_record.is_ready:
            report = ProblemReport(
                description={"en": "Connection invalid."}, who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        credential_exchange_record = await credential_manager.create_proposal(
            connection_id,
            comment=comment,
            credential_preview=context.message.credential_proposal,
            cred_def_id=credential_definition_id,
        )

        await responder.send(
            issue_credential.messages.credential_proposal.CredentialProposal(
                comment=context.message.comment,
                credential_proposal=context.message.credential_proposal,
                cred_def_id=credential_definition_id,
            ),
            connection_id=connection_id,
        )
        cred_exchange = CredExchange(record=credential_exchange_record)
        cred_exchange.assign_thread_from(context.message)
        await responder.send_reply(cred_exchange)

from typing import cast

from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.messaging.models.base import BaseModelError
from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.protocols.issue_credential.v1_0.manager import (
    CredentialManagerError,
)
from aries_cloudagent.protocols.issue_credential.v1_0.messages.credential_problem_report import (
    CredentialProblemReport,
)
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange as CredExRecord,
)
from aries_cloudagent.storage.error import StorageError
from marshmallow import fields

from ....util import (
    ExceptionReporter,
    admin_only,
    expand_message_class,
    get_connection,
    log_handling,
)
from .base import AdminHolderMessage
from .cred_offer_reject_sent import CredOfferRejectSent


@expand_message_class
class CredOfferReject(AdminHolderMessage):
    """Credential offer reject message."""

    message_type = "credential-offer-reject"

    class Fields:
        credential_exchange_id = fields.Str(
            required=True,
            description="ID of the credential exchange to reject.",
            example=UUIDFour.EXAMPLE,
        )

    def __init__(self, credential_exchange_id: str, **kwargs):
        super().__init__(**kwargs)
        self.credential_exchange_id = credential_exchange_id

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle credential offer reject message."""
        async with context.session() as session:
            async with ExceptionReporter(
                responder, (StorageError, CredentialManagerError, BaseModelError), self
            ):
                cred_ex_record = await CredExRecord.retrieve_by_id(
                    session, self.credential_exchange_id
                )
                cred_ex_record = cast(CredExRecord, cred_ex_record)
                connection_id = cred_ex_record.connection_id
                connection_record = await get_connection(session, connection_id)

        # TODO add credential_manager.reject(..) to ACA-Py

        cred_ex_record.state = (
            "reject-sent"  # TODO add CredExRecord.STATE_REJECT_SENT to ACA-Py
        )
        async with context.session() as session:
            await cred_ex_record.save(session, reason="Rejected credential offer.")

        problem_report = CredentialProblemReport(
            description={
                "en": "Rejected credential offer.",
                "code": "rejected",  # TODO add ProblemReportReason.REJECTED to ACA-Py
            }
        )
        problem_report.assign_thread_id(cred_ex_record.thread_id)

        sent = CredOfferRejectSent(**cred_ex_record.serialize())
        sent.assign_thread_from(self)

        await responder.send(
            problem_report, connection_id=connection_record.connection_id
        )
        await responder.send_reply(sent)

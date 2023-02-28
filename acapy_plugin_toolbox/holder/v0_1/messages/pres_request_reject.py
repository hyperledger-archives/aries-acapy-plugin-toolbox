from typing import cast

from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.protocols.present_proof.v1_0.messages.presentation_problem_report import (
    PresentationProblemReport,
)
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from aries_cloudagent.storage.error import StorageNotFoundError
from marshmallow import fields

from ....util import (
    ExceptionReporter,
    InvalidConnection,
    admin_only,
    expand_message_class,
    get_connection,
    log_handling,
)
from ..error import InvalidPresentationExchange
from .base import AdminHolderMessage
from .pres_reject_sent import PresRejectSent


@expand_message_class
class PresRequestReject(AdminHolderMessage):
    """Reject presentation request."""

    message_type = "presentation-request-reject"

    class Fields:
        presentation_exchange_id = fields.Str(
            required=True,
            description="Presentation request to reject.",
            example=UUIDFour.EXAMPLE,
        )
        message_description = fields.Str(
            required=False,
            description="Custom description of problem report",
        )

    def __init__(
        self, presentation_exchange_id: str, message_description: str = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.presentation_exchange_id = presentation_exchange_id
        self.message_description = message_description

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        async with context.session() as session:
            async with ExceptionReporter(
                responder,
                (InvalidPresentationExchange, InvalidConnection),
                context.message,
            ):
                try:
                    pres_ex_record = await PresExRecord.retrieve_by_id(
                        session, self.presentation_exchange_id
                    )
                    pres_ex_record = cast(PresExRecord, pres_ex_record)
                except StorageNotFoundError as err:
                    raise InvalidPresentationExchange(
                        "Presentation exchange ID not found"
                    ) from err

                connection_id = pres_ex_record.connection_id
                connection_record = await get_connection(session, connection_id)

        # TODO add presentation_manager.reject(..) to ACA-Py

        pres_ex_record.state = (
            "reject-sent"  # TODO add PresExRecord.STATE_REJECT_SENT to ACA-Py
        )
        async with context.session() as session:
            await pres_ex_record.save(session, reason="created problem report")

        problem_report = PresentationProblemReport(
            description={
                "en": self.message_description or "Rejected presentation request",
                "code": "rejected",  # TODO add ProblemReportReason.REJECTED to ACA-Py
            }
        )
        problem_report.assign_thread_id(pres_ex_record.thread_id)

        sent = PresRejectSent(pres_ex_record)
        sent.assign_thread_from(self)

        await responder.send(
            problem_report, connection_id=connection_record.connection_id
        )
        await responder.send_reply(sent)

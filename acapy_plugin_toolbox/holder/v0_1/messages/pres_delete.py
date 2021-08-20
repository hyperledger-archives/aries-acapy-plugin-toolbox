from typing import cast

from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from aries_cloudagent.storage.error import StorageNotFoundError
from marshmallow import fields

from ....util import ExceptionReporter, admin_only, expand_message_class, log_handling
from ..error import InvalidPresentationExchange
from .base import AdminHolderMessage
from .pres_deleted import PresDeleted


@expand_message_class
class PresDelete(AdminHolderMessage):
    """Delete a presentation exchange message."""

    message_type = "presentation-exchange-delete"

    class Fields:
        presentation_exchange_id = fields.Str(
            required=True,
            description="Presentation Exchange Message to delete.",
            example=UUIDFour.EXAMPLE,
        )

    def __init__(self, presentation_exchange_id: str, **kwargs):
        super().__init__(**kwargs)
        self.presentation_exchange_id = presentation_exchange_id

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        async with context.session() as session:
            async with ExceptionReporter(
                responder, InvalidPresentationExchange, context.message
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

            await pres_ex_record.delete_record(session)

        message = PresDeleted(presentation_exchange_id=self.presentation_exchange_id)
        message.assign_thread_from(self)
        await responder.send_reply(message)

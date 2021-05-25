from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchangeSchema as PresExRecordSchema,
)

from ....util import expand_message_class, with_generic_init
from .base import AdminHolderMessage


@with_generic_init
@expand_message_class
class PresRejectSent(AdminHolderMessage):
    """Presentation Exchange message."""

    message_type = "presentation-reject-sent"
    fields_from = PresExRecordSchema

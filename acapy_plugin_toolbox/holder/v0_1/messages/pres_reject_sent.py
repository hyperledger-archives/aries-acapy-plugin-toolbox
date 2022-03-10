from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange,
)
from marshmallow import fields

from ....util import expand_message_class
from .base import AdminHolderMessage


@expand_message_class
class PresRejectSent(AdminHolderMessage):
    """Presentation Exchange message."""

    message_type = "presentation-reject-sent"

    class Fields:
        presentation_exchange_id = fields.Str(
            required=True,
            description="Presentation request to reject.",
            example=UUIDFour.EXAMPLE,
        )
        raw_repr = fields.Mapping(required=True)

    def __init__(self, record: V10PresentationExchange, **kwargs):
        super().__init__(**kwargs)
        self.record = record
        self.raw_repr = record.serialize()
        self.presentation_exchange_id = record.presentation_exchange_id

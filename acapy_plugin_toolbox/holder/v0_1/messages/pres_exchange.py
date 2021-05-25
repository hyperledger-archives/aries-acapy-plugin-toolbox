from typing import Mapping

from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange,
)
from marshmallow import fields

from ....util import expand_message_class
from .base import AdminHolderMessage


@expand_message_class
class PresExchange(AdminHolderMessage):
    """Presentation Exchange message."""

    message_type = "presentation-exchange"

    class Fields:
        # TODO Use a toolbox PresentationExchangeRepresentation
        raw_repr = fields.Mapping(required=True)

    def __init__(self, record: V10PresentationExchange, **kwargs):
        super().__init__(**kwargs)
        self.record = record
        self.raw_repr = record.serialize()

    def serialize(self, **kwargs) -> Mapping:
        base_msg = super().serialize(**kwargs)
        return {**self.raw_repr, **base_msg}

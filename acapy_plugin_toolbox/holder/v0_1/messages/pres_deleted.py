from aries_cloudagent.messaging.valid import UUIDFour
from marshmallow import fields

from ....util import expand_message_class
from .base import AdminHolderMessage


@expand_message_class
class PresDeleted(AdminHolderMessage):
    """Presentation exchange message deleted."""

    message_type = "presentation-exchange-deleted"

    class Fields:
        presentation_exchange_id = fields.Str(
            required=True,
            description="Presentation Exchange Message to delete.",
            example=UUIDFour.EXAMPLE,
        )

    def __init__(self, presentation_exchange_id: str, **kwargs):
        super().__init__(**kwargs)
        self.presentation_exchange_id = presentation_exchange_id

from aries_cloudagent.messaging.valid import UUIDFour
from marshmallow import fields

from ....util import expand_message_class
from .base import AdminHolderMessage


@expand_message_class
class CredDeleted(AdminHolderMessage):
    """Credential deleted."""

    message_type = "credential-deleted"

    class Fields:
        credential_exchange_id = fields.Str(
            required=True,
            description="Credential exchange ID that was deleted.",
            example=UUIDFour.EXAMPLE,
        )
        credential_id = fields.Str(
            required=True,
            description="Credential ID that was deleted.",
            example=UUIDFour.EXAMPLE,
        )

    def __init__(self, credential_exchange_id: str, credential_id: str, **kwargs):
        super().__init__(**kwargs)
        self.credential_exchange_id = credential_exchange_id
        self.credential_id = credential_id

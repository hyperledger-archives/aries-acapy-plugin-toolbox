from typing import Any, Tuple

from aries_cloudagent.protocols.present_proof.v1_0.routes import IndyCredPrecisSchema
from marshmallow import fields

from ....decorators.pagination import Page
from ....util import expand_message_class, with_generic_init
from .base import AdminHolderMessage


@with_generic_init
@expand_message_class
class PresMatchingCredentials(AdminHolderMessage):
    """Presentation Matching Credentials"""

    message_type = "presentation-matching-credentials"

    class Fields:
        """Fields for MatchingCredentials."""

        presentation_exchange_id = fields.Str(
            required=True, description="Exchange ID for matched credentials."
        )
        matching_credentials = fields.Nested(
            IndyCredPrecisSchema, many=True, description="Matched credentials."
        )
        page = fields.Nested(
            Page.Schema,
            required=False,
            description="Pagination info for matched credentials.",
        )

    def __init__(
        self,
        presentation_exchange_id: str,
        matching_credentials: Tuple[Any, ...],
        page: Page = None,
        **kwargs,
    ):
        """Initialize PresMatchingCredentials"""
        super().__init__(**kwargs)
        self.presentation_exchange_id = presentation_exchange_id
        self.matching_credentials = matching_credentials
        self.page = page

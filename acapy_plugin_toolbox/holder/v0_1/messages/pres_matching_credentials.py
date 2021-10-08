from typing import Any, Tuple

from aries_cloudagent.protocols.present_proof.v1_0.routes import IndyCredPrecisSchema
from marshmallow import fields

from ....decorators.pagination import Page
from ....util import expand_message_class, with_generic_init
from .base import AdminHolderMessage
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)


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
        # TODO Use a toolbox PresentationExchangeRepresentation
        presentation_request = fields.Mapping(
            required=True,
            description="Presentation Request associated with the Presentation Exchange ID.",
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
        presentation_request: PresExRecord,
        matching_credentials: Tuple[Any, ...],
        page: Page = None,
        **kwargs,
    ):
        """Initialize PresMatchingCredentials"""
        super().__init__(**kwargs)
        self.presentation_exchange_id = presentation_exchange_id
        self.presentation_request = presentation_request
        self.matching_credentials = matching_credentials
        self.page = page

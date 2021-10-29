from aries_cloudagent.core.profile import Profile
from aries_cloudagent.indy.holder import IndyHolder
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from aries_cloudagent.protocols.present_proof.v1_0.routes import IndyCredPrecisSchema
from marshmallow import fields

from ....decorators.pagination import Page
from ....util import expand_message_class
from .base import AdminHolderMessage


class PresExRecordField(fields.Field):
    def _serialize(self, value: PresExRecord, attr, obj, **kwargs):
        return value.serialize()


@expand_message_class
class PresRequestReceived(AdminHolderMessage):
    """Presentation Request Received."""

    message_type = "presentation-request-received"

    DEFAULT_COUNT = 10

    class Fields:
        """Fields of Presentation request received message."""

        raw_repr = PresExRecordField(required=True, description="Presentation details.")
        presentation_exchange_id = fields.Str(
            required=True, description="Exchange ID for matched credentials."
        )
        # TODO Use a toolbox PresentationExchangeRepresentation
        presentation_request = fields.Mapping(
            required=True,
            description="Presentation Request associated with the Presentation Exchange ID.",
        )
        matching_credentials = fields.Nested(
            IndyCredPrecisSchema,
            many=True,
            description="Credentials matching the requested attributes.",
        )
        page = fields.Nested(
            Page.Schema, required=False, description="Pagination decorator."
        )

    def __init__(self, record: PresExRecord, **kwargs):
        super().__init__(**kwargs)
        self.raw_repr = record
        self.presentation_request = record.presentation_request.serialize()
        self.presentation_exchange_id = record.presentation_exchange_id
        self.matching_credentials = []
        self.page = None

    async def retrieve_matching_credentials(self, profile: Profile):
        holder = profile.inject(IndyHolder)
        request = self.presentation_request

        if not (type(request) is dict):
            request = request.serialize()

        self.matching_credentials = (
            await holder.get_credentials_for_presentation_request_by_referent(
                request,
                (),
                0,
                self.DEFAULT_COUNT,
                extra_query={},
            )
        )
        self.page = Page(count_=self.DEFAULT_COUNT, offset=self.DEFAULT_COUNT)

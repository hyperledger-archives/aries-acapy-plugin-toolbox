from aries_cloudagent.core.profile import Profile
from aries_cloudagent.indy.holder import IndyHolder
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchangeSchema as PresExRecordSchema,
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

        record = PresExRecordField(required=True, description="Presentation details.")
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
        self.record = record
        self.matching_credentials = []
        self.page = None

    async def retrieve_matching_credentials(self, profile: Profile):
        holder = profile.inject(IndyHolder)
        self.matching_credentials = (
            await holder.get_credentials_for_presentation_request_by_referent(
                self.record.presentation_request,
                (),
                0,
                self.DEFAULT_COUNT,
                extra_query={},
            )
        )
        self.page = Page(count_=self.DEFAULT_COUNT, offset=self.DEFAULT_COUNT)

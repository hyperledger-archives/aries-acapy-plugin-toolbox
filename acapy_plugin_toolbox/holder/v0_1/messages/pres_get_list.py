from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from marshmallow import fields

from ....decorators.pagination import Paginate
from ....util import admin_only, expand_message_class, log_handling
from .base import AdminHolderMessage
from .pres_list import PresList


@expand_message_class
class PresGetList(AdminHolderMessage):
    """Presentation get list message."""

    message_type = "presentations-get-list"

    class Fields:
        """Message fields."""

        connection_id = fields.Str(
            required=False, description="Filter presentations by connection_id"
        )
        paginate = fields.Nested(
            Paginate.Schema,
            required=False,
            data_key="~paginate",
            missing=Paginate(limit=10, offset=0),
            description="Pagination decorator.",
        )

    def __init__(self, connection_id: str = None, paginate: Paginate = None, **kwargs):
        super().__init__(**kwargs)
        self.connection_id = connection_id
        self.paginate = paginate or Paginate()

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""

        session = await context.session()
        paginate: Paginate = context.message.paginate

        post_filter_positive = dict(
            filter(
                lambda item: item[1] is not None,
                {
                    "role": PresExRecord.ROLE_PROVER,
                    "connection_id": context.message.connection_id,
                }.items(),
            )
        )
        records = await PresExRecord.query(
            session, {}, post_filter_positive=post_filter_positive
        )
        records, page = paginate.apply(records)
        pres_list = PresList([record.serialize() for record in records], page=page)
        await responder.send_reply(pres_list)

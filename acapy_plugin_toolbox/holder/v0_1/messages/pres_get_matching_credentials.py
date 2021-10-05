from typing import cast

from aries_cloudagent.indy.holder import IndyHolder
from aries_cloudagent.indy.sdk.holder import IndySdkHolder
from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.messaging.valid import UUIDFour
from marshmallow import fields

from ....decorators.pagination import Page, Paginate
from ....util import ExceptionReporter, admin_only, expand_message_class, log_handling
from ..error import InvalidPresentationExchange
from .base import AdminHolderMessage
from .pres_matching_credentials import PresMatchingCredentials
from .pres_request_approve import PresRequestApprove


@expand_message_class
class PresGetMatchingCredentials(AdminHolderMessage):
    """Retrieve matching credentials for a presentation request."""

    message_type = "presentation-get-matching-credentials"

    class Fields:
        presentation_exchange_id = fields.Str(
            required=True,
            description="Presentation to match credentials to.",
            example=UUIDFour.EXAMPLE,
        )
        paginate = fields.Nested(
            Paginate.Schema,
            required=False,
            data_key="~paginate",
            missing=Paginate(limit=10, offset=0),
            description="Pagination decorator.",
        )

    def __init__(
        self, presentation_exchange_id: str, paginate: Paginate = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.presentation_exchange_id = presentation_exchange_id
        self.paginate = paginate

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        holder = cast(IndySdkHolder, context.inject(IndyHolder))
        async with context.session() as session:
            async with ExceptionReporter(
                responder, InvalidPresentationExchange, context.message
            ):
                pres_ex_record = await PresRequestApprove.get_pres_ex_record(
                    session, self.presentation_exchange_id
                )

        matches = PresMatchingCredentials(
            presentation_exchange_id=self.presentation_exchange_id,
            matching_credentials=await holder.get_credentials_for_presentation_request_by_referent(
                pres_ex_record.presentation_request,
                (),
                self.paginate.offset,
                self.paginate.limit,
                extra_query={},
            ),
            presentation_request=pres_ex_record.presentation_request,
            page=Page(count_=self.paginate.limit, offset=self.paginate.offset),
        )
        matches.assign_thread_from(self)
        await responder.send_reply(matches)

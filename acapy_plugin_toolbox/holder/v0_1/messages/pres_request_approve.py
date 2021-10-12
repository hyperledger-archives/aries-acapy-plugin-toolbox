from typing import cast

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.indy.holder import IndyHolderError
from aries_cloudagent.indy.models.requested_creds import (
    IndyRequestedCredsRequestedAttrSchema,
    IndyRequestedCredsRequestedPredSchema,
)
from aries_cloudagent.ledger.error import LedgerError
from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.messaging.models.base import BaseModelError
from aries_cloudagent.protocols.present_proof.v1_0.manager import PresentationManager
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from aries_cloudagent.storage.error import StorageError, StorageNotFoundError
from aries_cloudagent.wallet.error import WalletNotFoundError
from marshmallow import fields

from ....util import (
    ExceptionReporter,
    InvalidConnection,
    admin_only,
    expand_message_class,
    get_connection,
    log_handling,
)
from ..error import InvalidPresentationExchange
from .base import AdminHolderMessage
from .pres_sent import PresSent


@expand_message_class
class PresRequestApprove(AdminHolderMessage):
    """Approve presentation request."""

    message_type = "presentation-request-approve"

    class Fields:
        """Fields on pres request approve message."""

        presentation_exchange_id = fields.Str(required=True)
        self_attested_attributes = fields.Dict(
            description="Self-attested attributes to build into proof",
            required=True,
            keys=fields.Str(example="attr_name"),  # marshmallow/apispec v3.0 ignores
            values=fields.Str(
                example="self_attested_value",
                description=(
                    "Self-attested attribute values to use in requested-credentials "
                    "structure for proof construction"
                ),
            ),
        )
        requested_attributes = fields.Dict(
            description=(
                "Nested object mapping proof request attribute referents to "
                "requested-attribute specifiers"
            ),
            required=True,
            keys=fields.Str(
                example="attr_referent"
            ),  # marshmallow/apispec v3.0 ignores
            values=fields.Nested(IndyRequestedCredsRequestedAttrSchema()),
        )
        requested_predicates = fields.Dict(
            description=(
                "Nested object mapping proof request predicate referents to "
                "requested-predicate specifiers"
            ),
            required=True,
            keys=fields.Str(
                example="pred_referent"
            ),  # marshmallow/apispec v3.0 ignores
            values=fields.Nested(IndyRequestedCredsRequestedPredSchema()),
        )
        comment = fields.Str(
            required=False,
            description="Optional comment.",
            example="Nothing to see here.",
        )

    def __init__(
        self,
        presentation_exchange_id: str,
        self_attested_attributes: dict,
        requested_attributes: dict,
        requested_predicates: dict,
        comment: str = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.presentation_exchange_id = presentation_exchange_id
        self.self_attested_attributes = self_attested_attributes
        self.requested_attributes = requested_attributes
        self.requested_predicates = requested_predicates
        self.comment = comment

    @staticmethod
    async def get_pres_ex_record(
        session: ProfileSession, pres_ex_id: str
    ) -> PresExRecord:
        """Retrieve a presentation exchange record and validate its state."""
        try:
            pres_ex_record = await PresExRecord.retrieve_by_id(session, pres_ex_id)
            pres_ex_record = cast(PresExRecord, pres_ex_record)
        except StorageNotFoundError as err:
            raise InvalidPresentationExchange(
                "Presentation exchange ID not found"
            ) from err

        if pres_ex_record.state != (PresExRecord.STATE_REQUEST_RECEIVED):
            raise InvalidPresentationExchange(
                "Presentation must be in request received state"
            )

        return pres_ex_record

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle presentation request approved message."""
        async with context.session() as session:
            async with ExceptionReporter(
                responder, InvalidPresentationExchange, context.message
            ):
                pres_ex_record = await self.get_pres_ex_record(
                    session, self.presentation_exchange_id
                )

            async with ExceptionReporter(responder, InvalidConnection, context.message):
                conn_record = await get_connection(
                    session, pres_ex_record.connection_id
                )

        presentation_manager = PresentationManager(context.profile)
        async with ExceptionReporter(
            responder,
            (
                BaseModelError,
                IndyHolderError,
                LedgerError,
                StorageError,
                WalletNotFoundError,
            ),
            context.message,
        ):
            pres_ex_record, message = await presentation_manager.create_presentation(
                pres_ex_record,
                {
                    "self_attested_attributes": self.self_attested_attributes,
                    "requested_attributes": self.requested_attributes,
                    "requested_predicates": self.requested_predicates,
                },
                comment=self.comment,
            )

        await responder.send(message, connection_id=conn_record.connection_id)

        presentation_sent = PresSent(record=pres_ex_record)
        presentation_sent.assign_thread_from(self)
        await responder.send_reply(presentation_sent)

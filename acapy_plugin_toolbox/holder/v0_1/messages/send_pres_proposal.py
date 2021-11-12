from aries_cloudagent.indy.models.pres_preview import (
    IndyPresPreview as PresentationPreview,
)
from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.protocols.present_proof.v1_0.manager import PresentationManager
from aries_cloudagent.protocols.present_proof.v1_0.messages.presentation_proposal import (
    PresentationProposal,
)
from aries_cloudagent.protocols.present_proof.v1_0.routes import (
    V10PresentationProposalRequestSchema as PresentationProposalRequestSchema,
)

from ....util import (
    ExceptionReporter,
    InvalidConnection,
    admin_only,
    expand_message_class,
    get_connection,
    log_handling,
)
from .base import AdminHolderMessage
from .pres_exchange import PresExchange


@expand_message_class
class SendPresProposal(AdminHolderMessage):
    """Presentation proposal message."""

    message_type = "send-presentation-proposal"
    fields_from = PresentationProposalRequestSchema

    def __init__(
        self,
        *,
        connection_id: str = None,
        comment: str = None,
        presentation_proposal: PresentationPreview = None,
        auto_present: bool = None,
        trace: bool = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.connection_id = connection_id
        self.comment = comment
        self.presentation_proposal = presentation_proposal
        self.auto_present = auto_present
        self.trace = trace

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send presentation proposal request."""
        session = await context.session()
        connection_id = str(context.message.connection_id)
        async with ExceptionReporter(responder, InvalidConnection, context.message):
            await get_connection(session, connection_id)

        comment = context.message.comment
        # Aries#0037 calls it a proposal in the proposal struct but it's of type preview
        presentation_proposal = PresentationProposal(
            comment=comment, presentation_proposal=context.message.presentation_proposal
        )
        auto_present = context.message.auto_present or context.settings.get(
            "debug.auto_respond_presentation_request"
        )

        presentation_manager = PresentationManager(context.profile)

        presentation_exchange_record = (
            await presentation_manager.create_exchange_for_proposal(
                connection_id=connection_id,
                presentation_proposal_message=presentation_proposal,
                auto_present=auto_present,
            )
        )
        await responder.send(presentation_proposal, connection_id=connection_id)

        pres_exchange = PresExchange(record=presentation_exchange_record)
        pres_exchange.assign_thread_from(context.message)
        await responder.send_reply(pres_exchange)

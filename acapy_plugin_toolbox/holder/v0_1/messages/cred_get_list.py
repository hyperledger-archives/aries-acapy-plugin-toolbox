from typing import List, Optional

from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange as CredExRecord,
)
from marshmallow import fields, validate

from ....decorators.pagination import Paginate
from ....util import admin_only, expand_message_class, log_handling
from .base import AdminHolderMessage
from .cred_list import CredList


@expand_message_class
class CredGetList(AdminHolderMessage):
    """Credential list retrieval message."""

    message_type = "credentials-get-list"

    class Fields:
        """Credential get list fields."""

        paginate = fields.Nested(
            Paginate.Schema,
            required=False,
            data_key="~paginate",
            missing=Paginate(limit=10, offset=0),
            description="Pagination decorator.",
        )
        states = fields.List(
            fields.Str(required=True),
            required=False,
            example=["offer_received"],
            description="Filter listed credentials by state.",
            validate=validate.OneOf(
                [
                    CredExRecord.STATE_ACKED,
                    CredExRecord.STATE_CREDENTIAL_RECEIVED,
                    CredExRecord.STATE_ISSUED,
                    CredExRecord.STATE_OFFER_RECEIVED,
                    CredExRecord.STATE_OFFER_SENT,
                    CredExRecord.STATE_PROPOSAL_RECEIVED,
                    CredExRecord.STATE_PROPOSAL_SENT,
                    CredExRecord.STATE_REQUEST_RECEIVED,
                    CredExRecord.STATE_REQUEST_SENT,
                ]
            ),
        )

    def __init__(
        self, paginate: Paginate = None, states: Optional[List[str]] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.paginate = paginate
        self.states = states

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""
        session = await context.session()

        credentials = await CredExRecord.query(
            session, post_filter_positive={"role": CredExRecord.ROLE_HOLDER}
        )

        if self.states:
            credentials = [c for c in credentials if c.state in self.states]

        credentials, page = self.paginate.apply(credentials)

        cred_list = CredList(
            results=[credential.serialize() for credential in credentials], page=page
        )
        cred_list.assign_thread_from(context.message)  # self
        await responder.send_reply(cred_list)

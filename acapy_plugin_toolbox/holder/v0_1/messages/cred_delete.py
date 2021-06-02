from typing import cast

from aries_cloudagent.indy.holder import IndyHolder
from aries_cloudagent.indy.sdk.holder import IndySdkHolder
from aries_cloudagent.messaging.base_handler import BaseResponder, RequestContext
from aries_cloudagent.messaging.models.base import BaseModelError
from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.protocols.issue_credential.v1_0.manager import (
    CredentialManagerError,
)
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange as CredExRecord,
)
from aries_cloudagent.storage.error import StorageError
from marshmallow import fields

from ....util import ExceptionReporter, admin_only, expand_message_class, log_handling
from .base import AdminHolderMessage
from .cred_deleted import CredDeleted


@expand_message_class
class CredDelete(AdminHolderMessage):
    """Delete a credential."""

    message_type = "credential-delete"

    class Fields:
        credential_exchange_id = fields.Str(
            required=True,
            description="ID of the credential exchange to delete",
            example=UUIDFour.EXAMPLE,
        )

    def __init__(self, credential_exchange_id: str, **kwargs):
        super().__init__(**kwargs)
        self.credential_exchange_id = credential_exchange_id

    @log_handling
    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle delete credential message."""

        holder = cast(IndySdkHolder, context.inject(IndyHolder))
        async with context.session() as session:
            async with ExceptionReporter(
                responder,
                (StorageError, CredentialManagerError, BaseModelError),
                context.message,
            ):
                cred_ex_record = await CredExRecord.retrieve_by_id(
                    session, self.credential_exchange_id
                )
                cred_ex_record = cast(CredExRecord, cred_ex_record)

                await holder.delete_credential(cred_ex_record.credential_id)
                await cred_ex_record.delete_record(session)

        message = CredDeleted(
            credential_exchange_id=self.credential_exchange_id,
            credential_id=cred_ex_record.credential_id,
        )
        message.assign_thread_from(self)
        await responder.send_reply(message)

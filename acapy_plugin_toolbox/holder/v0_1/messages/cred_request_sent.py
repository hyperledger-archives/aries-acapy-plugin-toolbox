from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchangeSchema as CredExRecordSchema,
)

from ....util import expand_message_class, with_generic_init
from .base import AdminHolderMessage


@with_generic_init
@expand_message_class
class CredRequestSent(AdminHolderMessage):
    """Credential offer acceptance received and credential request sent."""

    message_type = "credential-request-sent"
    fields_from = CredExRecordSchema

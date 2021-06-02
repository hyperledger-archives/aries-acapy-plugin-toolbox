from typing import Mapping

from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange,
)
from marshmallow import fields

from ....util import expand_message_class
from .base import AdminHolderMessage


@expand_message_class
class CredExchange(AdminHolderMessage):
    """Credential exchange message."""

    message_type = "credential-exchange"

    class Fields:
        # TODO Use a toolbox CredentialRepresentation
        raw_repr = fields.Mapping(required=True)

    def __init__(self, record: V10CredentialExchange, **kwargs):
        super().__init__(**kwargs)
        self.raw_repr = record.serialize()

    def serialize(self, **kwargs) -> Mapping:
        base_msg = super().serialize(**kwargs)
        return {**self.raw_repr, **base_msg}

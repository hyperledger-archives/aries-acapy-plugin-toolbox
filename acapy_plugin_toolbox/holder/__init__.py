"""Holder admin protocol."""

# Shortcuts to deeply nested classes
from aries_cloudagent.protocols.issue_credential import \
    v1_0 as issue_credential
from aries_cloudagent.protocols.issue_credential.v1_0.manager import (
    CredentialManager, CredentialManagerError
)
from aries_cloudagent.protocols.issue_credential.v1_0.messages.inner.credential_preview import \
    CredAttrSpec as CredentialAttributeSpec
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import \
    V10CredentialExchange as CredExRecord
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import \
    V10CredentialExchangeSchema as CredExRecordSchema
from aries_cloudagent.protocols.issue_credential.v1_0.routes import \
    V10CredentialProposalRequestMandSchema as CredentialProposalRequestSchema
from aries_cloudagent.protocols.present_proof import v1_0 as present_proof
from aries_cloudagent.protocols.present_proof.v1_0.manager import (
    PresentationManager, PresentationManagerError
)
from aries_cloudagent.protocols.present_proof.v1_0.messages.inner.presentation_preview import (
    PresentationPreview
)
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import \
    V10PresentationExchange as PresExRecord
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import \
    V10PresentationExchangeSchema as PresExRecordSchema
from aries_cloudagent.protocols.present_proof.v1_0.routes import (
    IndyCredPrecisSchema
)
from aries_cloudagent.protocols.present_proof.v1_0.routes import \
    V10PresentationProposalRequestSchema as PresentationProposalRequestSchema

__all__ = [
    "issue_credential", "CredentialManager", "CredentialManagerError",
    "CredentialAttributeSpec", "CredExRecord", "CredExRecordSchema",
    "CredentialProposalRequestSchema", "present_proof",
    "PresentationManager", "PresentationManagerError",
    "PresentationPreview", "PresExRecord", "PresExRecordSchema", "IndyCredPrecisSchema",
    "PresentationProposalRequestSchema"
]

"""Load issuance plugins."""

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..credential_definitions import MESSAGE_TYPES as CRED_DEF_MESSAGES
from ..schemas import MESSAGE_TYPES as SCHEMA_MESSAGES
from ..dids import MESSAGE_TYPES as DID_MESSAGES
from ..issuer import MESSAGE_TYPES as ISSUER_MESSAGES

async def setup(context: InjectionContext):
    """Setup Toolbox Plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        CRED_DEF_MESSAGES,
        SCHEMA_MESSAGES,
        DID_MESSAGES,
        ISSUER_MESSAGES,
    )

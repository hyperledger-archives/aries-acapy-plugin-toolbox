"""Load holder plugins."""

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..credential_definitions import MESSAGE_TYPES as CRED_DEF_MESSAGES
from ..holder import MESSAGE_TYPES as HOLDER_MESSAGES

async def setup(context: InjectionContext):
    """Setup Toolbox Plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        CRED_DEF_MESSAGES,
        HOLDER_MESSAGES,
    )

"""Load connections plugins."""

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..connections import MESSAGE_TYPES as CONNECTION_MESSAGES
from ..static_connections import MESSAGE_TYPES as STATIC_CONN_MESSAGES

async def setup(context: InjectionContext):
    """Setup Toolbox Plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        CONNECTION_MESSAGES,
        STATIC_CONN_MESSAGES,
    )

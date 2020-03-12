"""Load connections plugins."""

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..connections import setup as connection_setup
from ..static_connections import setup as static_conn_setup
from ..invitations import setup as invitations_setup

async def setup(context: InjectionContext):
    """Setup Toolbox Plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    await connection_setup(context, protocol_registry)
    await static_conn_setup(context, protocol_registry)
    await invitations_setup(context, protocol_registry)
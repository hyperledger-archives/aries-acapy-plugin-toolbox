"""Load holder plugins."""

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..credential_definitions import setup as cred_def_setup
from ..holder import setup as holder_setup


async def setup(context: InjectionContext):
    """Setup Toolbox Plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    await cred_def_setup(context, protocol_registry)
    await holder_setup(context, protocol_registry)

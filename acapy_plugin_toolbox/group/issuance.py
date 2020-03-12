"""Load issuance plugins."""

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..credential_definitions import setup as cred_def_setup
from ..schemas import setup as schema_setup
from ..dids import setup as did_setup
from ..issuer import setup as issuer_setup


async def setup(context: InjectionContext):
    """Setup Toolbox Plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    await cred_def_setup(context, protocol_registry)
    await schema_setup(context, protocol_registry)
    await did_setup(context, protocol_registry)
    await issuer_setup(context, protocol_registry)

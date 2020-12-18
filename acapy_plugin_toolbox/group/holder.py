"""Load holder plugins."""

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..credential_definitions import setup as cred_def_setup
from ..holder import setup as holder_setup


async def setup(session: ProfileSession):
    """Setup Toolbox Plugin."""
    protocol_registry = session.inject(ProtocolRegistry)
    await cred_def_setup(session, protocol_registry)
    await holder_setup(session, protocol_registry)

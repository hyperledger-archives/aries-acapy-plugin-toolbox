"""Load connections plugins."""

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..connections import setup as connection_setup
from ..static_connections import setup as static_conn_setup
from ..invitations import setup as invitations_setup

async def setup(session: ProfileSession):
    """Setup Toolbox Plugin."""
    protocol_registry = session.inject(ProtocolRegistry)
    await connection_setup(session, protocol_registry)
    await static_conn_setup(session, protocol_registry)
    await invitations_setup(session, protocol_registry)

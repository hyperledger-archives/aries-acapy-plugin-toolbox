"""Load issuance plugins."""

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..credential_definitions import setup as cred_def_setup
from ..schemas import setup as schema_setup
from ..dids import setup as did_setup
from ..issuer import setup as issuer_setup


async def setup(session: ProfileSession):
    """Setup Toolbox Plugin."""
    protocol_registry = session.inject(ProtocolRegistry)
    await cred_def_setup(session, protocol_registry)
    await schema_setup(session, protocol_registry)
    await did_setup(session, protocol_registry)
    await issuer_setup(session, protocol_registry)

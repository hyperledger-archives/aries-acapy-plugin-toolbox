"""Load all plugins."""

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

from ..connections import setup as connection_setup
from ..credential_definitions import setup as cred_def_setup
from ..schemas import setup as schema_setup
from ..dids import setup as did_setup
from ..static_connections import setup as static_conn_setup
from ..holder import setup as holder_setup
from ..issuer import setup as issuer_setup
from ..basicmessage import setup as basic_message_setup
from ..taa import setup as taa_setup
#from ..payments import setup as payment_setup
from ..invitations import setup as invitations_setup
from ..mediator import setup as mediator_setup
from ..routing import setup as routing_setup

async def setup(session: ProfileSession):
    """Setup Toolbox Plugin."""
    protocol_registry = session.inject(ProtocolRegistry)
    await connection_setup(session, protocol_registry)
    await cred_def_setup(session, protocol_registry)
    await schema_setup(session, protocol_registry)
    await did_setup(session, protocol_registry)
    await static_conn_setup(session, protocol_registry)
    await holder_setup(session, protocol_registry)
    await issuer_setup(session, protocol_registry)
    await basic_message_setup(session, protocol_registry)
    await taa_setup(session, protocol_registry)
#    await payment_setup(session, protocol_registry)
    await invitations_setup(session, protocol_registry)
    await mediator_setup(session, protocol_registry)
    await routing_setup(session, protocol_registry)

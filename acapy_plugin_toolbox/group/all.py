"""Load all plugins."""

from aries_cloudagent.config.injection_context import InjectionContext
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

async def setup(context: InjectionContext):
    """Setup Toolbox Plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    await connection_setup(context, protocol_registry)
    await cred_def_setup(context, protocol_registry)
    await schema_setup(context, protocol_registry)
    await did_setup(context, protocol_registry)
    await static_conn_setup(context, protocol_registry)
    await holder_setup(context, protocol_registry)
    await issuer_setup(context, protocol_registry)
    await basic_message_setup(context, protocol_registry)
    await taa_setup(context, protocol_registry)
#    await payment_setup(context, protocol_registry)
    await invitations_setup(context, protocol_registry)
    await mediator_setup(context, protocol_registry)
    await routing_setup(context, protocol_registry)

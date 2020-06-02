from .basicmessage import MESSAGE_TYPES as BASIC_MESSAGE_MESSAGE_TYPES
from .connections_new import MESSAGE_TYPES as CONNECTION_NEW_MESSAGE_TYPES
from .connections import MESSAGE_TYPES as CONNECTIONS_MESSAGE_TYPES
from .credential_definitions import MESSAGE_TYPES as CREDENTIAL_DEFINITIONS_MESSAGE_TYPES
from .dids import MESSAGE_TYPES as DIDS_MESSAGE_TYPES
from .holder import MESSAGE_TYPES as HOLDER_MESSAGE_TYPES
from .invitations import MESSAGE_TYPES as INVITATIONS_MESSAGE_TYPES

from .issuer import MESSAGE_TYPES as ISSUER_MESSAGE_TYPES
from .payments import MESSAGE_TYPES as PAYMENTS_MESSAGE_TYPES
from .schemas import MESSAGE_TYPES as SCHEMAS_MESSAGE_TYPES
from .static_connections import MESSAGE_TYPES as STATIC_CONNECTIONS_MESSAGE_TYPES
from .taa import MESSAGE_TYPES as TAA_MESSAGE_TYPES

MESSAGE_TYPES = {}
MESSAGE_TYPES.update(BASIC_MESSAGE_MESSAGE_TYPES)
MESSAGE_TYPES.update(CONNECTION_NEW_MESSAGE_TYPES)
MESSAGE_TYPES.update(CONNECTIONS_MESSAGE_TYPES)
MESSAGE_TYPES.update(CREDENTIAL_DEFINITIONS_MESSAGE_TYPES)
MESSAGE_TYPES.update(DIDS_MESSAGE_TYPES)
MESSAGE_TYPES.update(HOLDER_MESSAGE_TYPES)
MESSAGE_TYPES.update(INVITATIONS_MESSAGE_TYPES)
MESSAGE_TYPES.update(ISSUER_MESSAGE_TYPES)
MESSAGE_TYPES.update(PAYMENTS_MESSAGE_TYPES)
MESSAGE_TYPES.update(SCHEMAS_MESSAGE_TYPES)
MESSAGE_TYPES.update(STATIC_CONNECTIONS_MESSAGE_TYPES)
MESSAGE_TYPES.update(TAA_MESSAGE_TYPES)

"""Payment plugin."""
import platform
from ctypes import cdll

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry

LIBRARY = 'libsovtoken'
EXTENSION = {
    "darwin": ".dylib",
    "linux": ".so",
    "win32": ".dll",
    'windows': '.dll'
}


PROTOCOL_URI = (
    'https://github.com/hyperledger/aries-toolbox/'
    'tree/master/docs/admin-payments/0.1'
)

GET_ADDRESS_LIST = f'{PROTOCOL_URI}/get-address-list'
ADDRESS_LIST = f'{PROTOCOL_URI}/address-list'
CREATE_ADDRESS = f'{PROTOCOL_URI}/create-address'
ADDRESS = f'{PROTOCOL_URI}/address'
TRANSFER_UTX = f'{PROTOCOL_URI}/transfer-utx'
UTX = f'{PROTOCOL_URI}/utx'
MESSAGE_TYPES = {
    GET_ADDRESS_LIST: 'acapy_plugin_toolbox.payments.GetAddressList'
    ADDRESS_LIST: 'acapy_plugin_toolbox.payments.ADDRESS_LIST'
    CREATE_ADDRESS: 'acapy_plugin_toolbox.payments.CREATE_ADDRESS'
    ADDRESS: 'acapy_plugin_toolbox.payments.ADDRESS' 
    TRANSFER_UTX: 'acapy_plugin_toolbox.payments.TRANSFER_UTX'
    UTX: 'acapy_plugin_toolbox.payments.UTX' 

}


def file_ext():
    """Determine extension for system."""
    your_platform = platform.system().lower()
    return EXTENSION[your_platform] if (your_platform in EXTENSION) else '.so'


async def setup(context: InjectionContext):
    """Load plugin."""

    # Load in libsovtoken
    cdll.LoadLibrary(LIBRARY + file_ext()).sovtoken_init()

    protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )

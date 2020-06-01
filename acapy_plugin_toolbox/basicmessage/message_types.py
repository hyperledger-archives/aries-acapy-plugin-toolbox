PROTOCOL_URI = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/basicmessage/1.0"
BASIC_MESSAGE = f"{PROTOCOL_URI}/message"

ADMIN_PROTOCOL_URI = (
    "https://github.com/hyperledger/"
    "aries-toolbox/tree/master/docs/admin-basicmessage/0.1"
)
GET = f"{ADMIN_PROTOCOL_URI}/get"
SEND = f"{ADMIN_PROTOCOL_URI}/send"
DELETE = f"{ADMIN_PROTOCOL_URI}/delete"
NEW = f"{ADMIN_PROTOCOL_URI}/new"

MESSAGE_TYPES = {
    BASIC_MESSAGE: "acapy_plugin_toolbox.basicmessage.BasicMessage",
    GET: "acapy_plugin_toolbox.basicmessage.Get",
    SEND: "acapy_plugin_toolbox.basicmessage.Send",
    DELETE: "acapy_plugin_toolbox.basicmessage.Delete",
}

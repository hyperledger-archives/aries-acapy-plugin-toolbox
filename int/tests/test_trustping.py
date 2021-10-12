"""Trust Ping Tests"""
import pytest
from acapy_client import Client
from acapy_client.api.connection import (
    create_invitation,
    delete_connection,
    get_connections,
    receive_invitation,
)
from acapy_client.models.create_invitation_request import CreateInvitationRequest
from acapy_client.models.receive_invitation_request import ReceiveInvitationRequest


@pytest.fixture
def new_connection(
    backchannel: Client, wait_for_message, asynchronously_received_messages
):
    """Factory for new connections."""

    async def _new_connection():
        await asynchronously_received_messages()
        lhs_conn = await create_invitation.asyncio(
            client=backchannel, json_body=CreateInvitationRequest(), auto_accept="true"
        )
        rhs_conn = await receive_invitation.asyncio(
            client=backchannel,
            json_body=ReceiveInvitationRequest.from_dict(lhs_conn.invitation.to_dict()),
            auto_accept="true",
        )
        first_connected = await wait_for_message(
            msg_type="https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/connected"
        )
        second_connected = await wait_for_message(
            msg_type="https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/connected"
        )
        return (lhs_conn.connection_id, rhs_conn.connection_id)

    yield _new_connection


@pytest.fixture(autouse=True)
async def clear_connection_state(backchannel: Client, connection_id: str):
    """Clear connections after each test."""
    yield
    connections = await get_connections.asyncio(client=backchannel)
    for connection in connections.results:
        if connection.connection_id != connection_id:
            await delete_connection.asyncio(
                client=backchannel, conn_id=connection.connection_id
            )


@pytest.mark.asyncio
async def test_send_trustping(connection, new_connection, wait_for_message):
    """Create a connection and send a trust ping"""
    conn = await new_connection()
    ping = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-trustping/0.1/send",
            "connection_id": conn[0],
            "comment": "Trust ping test",
        },
    )
    assert (
        ping["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-trustping/0.1/sent"
    )
    await wait_for_message(
        msg_type="https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-trustping/0.1/response-received"
    )

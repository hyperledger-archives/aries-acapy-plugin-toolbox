"""Connections Tests"""
from acapy_client import Client
from acapy_client.api.connection import (
    create_invitation,
    delete_connection,
    get_connections,
    receive_invitation,
)
from acapy_client.models.create_invitation_request import CreateInvitationRequest
from acapy_client.models.receive_invitation_request import ReceiveInvitationRequest
from echo_agent import EchoClient
from echo_agent.models import ConnectionInfo
import pytest


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
async def test_create_connection(connection, wait_for_message):
    """Send an invitation and receive it to create a new connection"""
    msg_invitation = {
        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
        "alias": "Invitation I sent to Alice",
        "label": "Bob",
        "group": "default",
        "auto_accept": True,
        "multi_use": True,
    }
    invitation = await connection.send_and_await_reply_async(msg_invitation)
    msg_received = {
        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
        "invitation": invitation["invitation_url"],
        "auto_accept": True,
    }
    received = await connection.send_and_await_reply_async(msg_received)
    message = await wait_for_message(
        msg_type="https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/connected"
    )
    assert (
        received["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/connection"
    )
    assert received["label"] == msg_invitation["label"]


@pytest.mark.asyncio
async def test_get_list(connection, new_connection):
    """Create two connections and verify that their connection_ids are in connections list"""
    conn1 = await new_connection()
    conn2 = await new_connection()
    get_list = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
        }
    )
    assert (
        get_list["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/list"
    )
    assert conn1[0] in [
        connection_item["connection_id"] for connection_item in get_list["connections"]
    ]
    assert conn2[0] in [
        connection_item["connection_id"] for connection_item in get_list["connections"]
    ]


@pytest.mark.asyncio
async def test_update(connection, new_connection):
    """Test update of connection attribute"""
    conn = await new_connection()
    msg_update = {
        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/update",
        "connection_id": conn[0],
        "label": "Updated label",
        "role": "Updated role",
    }
    update = await connection.send_and_await_reply_async(msg_update)
    assert update["label"] == "Updated label"


@pytest.mark.asyncio
async def test_delete(connection, new_connection):
    """Create an invitation, delete it, and verify that its label and connection_id
    is no longer in the connections list"""
    conn = await new_connection()
    delete_connection = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/delete",
            "connection_id": conn[0],
        }
    )
    assert (
        delete_connection["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/deleted"
    )
    assert delete_connection["connection_id"] == conn[0]
    get_list = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
        }
    )
    assert conn[0] not in [
        connection_item["connection_id"] for connection_item in get_list["connections"]
    ]

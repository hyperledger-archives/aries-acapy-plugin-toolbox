"""Connections Tests"""
import asyncio
import pytest
from acapy_backchannel import Client
from acapy_backchannel.api.connection import delete_connection, get_connections
from aries_staticagent import Message


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
async def test_create_connection(connection):
    """Send an invitation and receive it to create a new connection"""
    msg_invitation = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        })
    invitation = await connection.send_and_await_reply_async(
        msg_invitation,
        condition=lambda reply: reply.thread["thid"] == msg_invitation.id,
        return_route="all",
    )
    msg_received = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
            "invitation": invitation["invitation_url"],
            "auto_accept": True,
        })
    received = await connection.send_and_await_reply_async(
        msg_received,
        condition=lambda reply: reply.thread["thid"] == msg_received.id
    )
    assert (
        received["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/connection"
    )
    assert received["label"] == msg_invitation["label"]


@pytest.mark.asyncio
async def test_get_list(connection):
    """Create two connections and verify that their connection_ids are in connections list"""
    msg_invitation = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        })
    invitation = await connection.send_and_await_reply_async(
        msg_invitation,
        condition=lambda reply: reply.thread["thid"] == msg_invitation.id,
        return_route="all",
    )
    msg_received = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
            "invitation": invitation["invitation_url"],
            "auto_accept": True,
        })
    received = await connection.send_and_await_reply_async(
        msg_received,
        condition=lambda reply: reply.thread["thid"] == msg_received.id
    )
    msg_invitation2 = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Second invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        })
    invitation2 = await connection.send_and_await_reply_async(
        msg_invitation2,
        condition=lambda reply: reply.thread["thid"] == msg_invitation2.id,
        return_route="all",
    )
    msg_received2 = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
            "invitation": invitation2["invitation_url"],
            "auto_accept": True,
        })
    received2 = await connection.send_and_await_reply_async(
        msg_received2,
        condition=lambda reply: reply.thread["thid"] == msg_received2.id
    )
    get_list = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
        }
    )
    assert (get_list["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/list"
    )
    assert received["connection_id"] in [connection_item["connection_id"] for connection_item in get_list["connections"]]
    assert received2["connection_id"] in [connection_item["connection_id"] for connection_item in get_list["connections"]]


@pytest.mark.asyncio
async def test_update(connection):
    """Test update of connection attribute"""
    msg_invitation = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        })
    invitation = await connection.send_and_await_reply_async(
        msg_invitation,
        condition=lambda reply: reply.thread["thid"] == msg_invitation.id,
        return_route="all",
    )
    msg_received = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
            "invitation": invitation["invitation_url"],
            "auto_accept": True,
        })
    received = await connection.send_and_await_reply_async(
        msg_received,
        condition=lambda reply: reply.thread["thid"] == msg_received.id,
    )
    msg_update = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/update",
            "connection_id": received["connection_id"],
            "label": "Updated label",
            "role": "Updated role",
        })
    update = await connection.send_and_await_reply_async(
        msg_update,
        condition=lambda reply: reply.thread["thid"] == msg_update.id,
    )
    assert update["label"] == "Updated label"


@pytest.mark.asyncio
async def test_delete(connection):
    """Create an invitation, delete it, and verify that its label and connectio_id
    is no longer in the connections list"""
    invitation_msg = Message(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        }
    )
    invitation = await connection.send_and_await_reply_async(
        invitation_msg,
        condition=lambda reply: reply.thread["thid"] == invitation_msg.id,
        return_route="all",
    )
    msg_received = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
            "invitation": invitation["invitation_url"],
            "auto_accept": True,
        })
    received = await connection.send_and_await_reply_async(
        msg_received,
        condition=lambda reply: reply.thread["thid"] == msg_received.id,
    )
    delete_connection = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/delete",
            "connection_id": received["connection_id"],
        }
    )
    assert delete_connection["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/deleted"
    assert delete_connection["connection_id"] == received["connection_id"]
    get_list = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
        }
    )
    assert invitation_msg["label"] not in [connection_item["label"] for connection_item in get_list["connections"]]
    assert received["connection_id"] not in [connection_item["connection_id"] for connection_item in get_list["connections"]]

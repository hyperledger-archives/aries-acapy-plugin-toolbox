"""Invitations tests"""
import pytest
from acapy_client import Client
from acapy_client.api.connection import delete_connection, get_connections


@pytest.fixture(autouse=True)
async def clear_invitation_state(backchannel: Client, connection_id: str):
    """Clear invitation after each test."""
    yield
    connections = await get_connections.asyncio(client=backchannel)
    for connection in connections.results:
        if connection.state == "invitation":
            await delete_connection.asyncio(
                client=backchannel, conn_id=connection.connection_id
            )


@pytest.mark.asyncio
async def test_create_invitation(connection):
    """Test create invitation protocol"""
    reply = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        },
        return_route="all",
    )
    assert (
        reply["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/invitation"
    )


@pytest.mark.asyncio
async def test_get_list(connection):
    """Test get list protocol"""
    reply = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/get-list"
        },
        return_route="all",
    )
    assert (
        reply["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/list"
    )


@pytest.mark.asyncio
async def test_num_results(connection):
    """Test that the create message protocol causes new item in results list"""
    # Input number of messages to add to the list
    added_num = 2
    for i in range(added_num):
        await connection.send_and_await_reply_async(
            {
                "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
                "alias": "Message I sent to Alice",
                "label": "Bob",
                "group": "admin",
                "auto_accept": True,
                "multi_use": True,
            },
            return_route="all",
        )
    reply = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/get-list"
        },
        return_route="all",
    )
    assert len(reply["results"]) == added_num


@pytest.mark.asyncio
async def test_empty_list(connection):
    """Test that get-list returns no results if no create messages have been sent"""
    reply = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/get-list"
        },
        return_route="all",
    )
    assert reply["results"] == []

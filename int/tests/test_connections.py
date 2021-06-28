"""Connection Tests"""
import asyncio
import pytest
from acapy_backchannel import Client
from acapy_backchannel.api.connection import delete_connection, get_connections
import time
from aries_staticagent import Message


@pytest.mark.asyncio
async def clear_connections(client: Client):
    """Clear all connections, if any."""
    connections = await get_connections.asyncio(client=client)
    for connection in connections.results:
        if connection.state == "connection":
            await delete_connection.asyncio(
                client=client, conn_id=connection.connection_id
            )


@pytest.mark.asyncio
@pytest.fixture(autouse=True)
async def clear_connection_state(backchannel: Client):
    """Clear invitations after each test."""
    # yield
    # await clear_connections(backchannel)
    yield await clear_connections(backchannel)


# Temporary Test: before connection
# @pytest.mark.asyncio
# async def test_get_list_before_connection(connection):
#     get_list_before_connection = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
#         }
#     )
#     print("get_list before connection: ", get_list_before_connection["connections"])
#     assert True  # False


@pytest.mark.asyncio
async def test_create_connection(connection):
    """Send an invitation and receive it to create a new connection"""
    sent_invitation = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        })
    invitation = await connection.send_and_await_reply_async(
        sent_invitation,
        condition=lambda reply: reply.thread["thid"] == sent_invitation.id,
        return_route="all",
    )
    sent_msg = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
            "invitation": invitation["invitation_url"],
            "auto_accept": True,
        })
    received = await connection.send_and_await_reply_async(
        sent_msg,
        condition=lambda reply: reply.thread["thid"] == sent_msg.id
    )
    assert (
        received["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/connection"
    )


# # Temporary Test: after connection
# @pytest.mark.asyncio
# async def test_get_list_after_connection(connection):
#     get_list_after_connection = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
#         }
#     )
#     print("get_list after connection: ", get_list_after_connection["connections"])
#     assert True  # False


@pytest.mark.asyncio
async def test_get_list(connection):
    sent_invitation = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        })
    invitation = await connection.send_and_await_reply_async(
        sent_invitation,
        condition=lambda reply: reply.thread["thid"] == sent_invitation.id,
        return_route="all",
    )
    sent_msg = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
            "invitation": invitation["invitation_url"],
            "auto_accept": True,
        })
    received = await connection.send_and_await_reply_async(
        sent_msg,
        condition=lambda reply: reply.thread["thid"] == sent_msg.id
    )
    sent_invitation2 = Message({
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Second invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
        })
    invitation2 = await connection.send_and_await_reply_async(
        sent_invitation2,
        condition=lambda reply: reply.thread["thid"] == sent_invitation2.id,
        return_route="all",
    )
    sent_msg2 = {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
            "invitation": invitation2["invitation_url"],
            "auto_accept": True,
        }
    received2 = await connection.send_and_await_reply_async(
        sent_msg2,
        condition=lambda reply: reply.thread["thid"] == sent_msg2.id
    )
    get_list = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
        }
    )
    assert (
        get_list["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/list"
    )


# @pytest.mark.asyncio
# async def test_update(connection):
#     """Update connection attribute"""
#     invitation = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
#             "alias": "Invitation I sent to Alice",
#             "label": "Bob",
#             "group": "admin",
#             "auto_accept": True,
#             "multi_use": True,
#         },
#         return_route="all",
#     )
#     received = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
#             "invitation": invitation["invitation_url"],
#             "auto_accept": True,
#         }
#     )
#     update = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/update",
#             "connection_id": received["connection_id"],
#             "label": "Updated label",
#             "role": "Updated role",
#         }
#     )
#     assert update["label"] == "Updated label"


# @pytest.mark.asyncio
# async def test_delete(connection):
#     invitation = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
#             "alias": "Invitation I sent to Alice",
#             "label": "Bob",
#             "group": "admin",
#             "auto_accept": True,
#             "multi_use": True,
#         },
#         return_route="all",
#     )
#     received = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-invitation",
#             "invitation": invitation["invitation_url"],
#             "auto_accept": True,
#         }
#     )
#     get_list_beforedelete = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
#         }
#     )
#     print("Connections before delete: ", get_list_beforedelete["connections"])
#     assert (
#         received["@type"]
#         == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/connection"
#     )
#     delete_connection = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/delete",
#             "connection_id": received["connection_id"],
#         }
#     )
#     get_list_afterdelete = await connection.send_and_await_reply_async(
#         {
#             "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/get-list"
#         }
#     )
#     print("List after delete", get_list_afterdelete["connections"])
#     # for i in get_list_beforedelete["connections"]:
#     #     if i not in get_list_afterdelete["connections"]:
#     #         print(i)
#     assert (
#         delete_connection["@type"]
#         == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/deleted"
#     )

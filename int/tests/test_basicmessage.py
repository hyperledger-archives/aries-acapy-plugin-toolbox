"""Basic Message Tests"""
import asyncio
import pytest
from aries_staticagent import StaticConnection, utils


@pytest.mark.asyncio
async def test_send(connection: StaticConnection, connection_id: str):
    """Test send message"""
    with connection.next() as future_recip_message:
        sent_message = await asyncio.wait_for(
            connection.send_and_await_reply_async(
                {
                    "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                    "connection_id": connection_id,
                    "content": "Your hovercraft is full of eels.",
                },
                return_route="all",
            ),
            timeout=60,
        )
        recip_message = await asyncio.wait_for(future_recip_message, 60)
    assert (
        recip_message["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/sent"
    )
    assert recip_message["message"]["content"] == "Your hovercraft is full of eels."
    # TODO add proper backchannel for clearing messages 
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete",
        }
    )


@pytest.mark.asyncio
async def test_new(connection: StaticConnection):
    """Test new message notification"""
    new_response = await connection.send_and_await_reply_async(
                {
                    "@type": "https://didcomm.org/basicmessage/1.0/message",
                    "~l10n": { "locale": "en" },
                    "sent_time": utils.timestamp(),
                    "content": "Your hovercraft is full of eels."
                },
                return_route="all",
            )
    assert new_response["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/new"
    assert new_response["message"]["content"] == "Your hovercraft is full of eels."
    # Delete messages to clear the state between tests
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete",
        }
    )


@pytest.mark.asyncio
async def test_get(connection: StaticConnection, connection_id: str):
    """Send multiple messages and verify that the proper count and content appears in messages list"""
    with connection.next() as future_recip_message:
        sent_message = await asyncio.wait_for(
            connection.send_and_await_reply_async(
                {
                    "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                    "connection_id": connection_id,
                    "content": "Are you suggesting coconuts migrate?",
                },
                return_route="all",
            ),
            timeout=60,
        )
        recip_message = await asyncio.wait_for(future_recip_message, 60)
    with connection.next() as future_recip_message:
        sent_message = await asyncio.wait_for(
            connection.send_and_await_reply_async(
                {
                    "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                    "connection_id": connection_id,
                    "content": "'Tis but a flesh wound.",
                },
                return_route="all",
            ),
            timeout=60,
        )
        recip_message = await asyncio.wait_for(future_recip_message, 60)
    get_messages = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/get",
        }
    )
    assert (
        get_messages["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/messages"
    )
    assert get_messages["count"] == 2
    assert get_messages["messages"][1]["content"] == "Are you suggesting coconuts migrate?"
    assert get_messages["messages"][0]["content"] == "'Tis but a flesh wound."
    # Delete messages to clear the state between tests
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete",
        }
    )


@pytest.mark.asyncio
async def test_get_limit_offset(connection: StaticConnection, connection_id: str):
    """Send multiple messages and verify that get returns the correct content according to the limit and offset"""
    for i in range(6):
        with connection.next() as future_recip_message:
            sent_message = await asyncio.wait_for(
                connection.send_and_await_reply_async(
                    {
                        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                        "connection_id": connection_id,
                        "content": "Test Message #{}".format(i),
                    },
                    return_route="all",
                ),
                timeout=60,
            )
            recip_message = await asyncio.wait_for(future_recip_message, 60)
    get_messages = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/get",
            "limit": 3,
            "offset": 2,
        }
    )
    assert (
        get_messages["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/messages"
    )
    assert get_messages["count"] == 3
    assert get_messages["messages"][0]["content"] == "Test Message #3"
    assert get_messages["messages"][1]["content"] == "Test Message #2"
    assert get_messages["messages"][2]["content"] == "Test Message #1"
    # Delete messages to clear the state between tests
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete",
        }
    )


@pytest.mark.asyncio
async def test_delete(connection: StaticConnection, connection_id: str):
    """Send multiple messages, delete them, and verify that the messages count is zero"""
    for i in range(6):
        with connection.next() as future_recip_message:
            sent_message = await asyncio.wait_for(
                connection.send_and_await_reply_async(
                    {
                        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                        "connection_id": connection_id,
                        "content": "Test Message #{}".format(i),
                    },
                    return_route="all",
                ),
                timeout=60,
            )
            recip_message = await asyncio.wait_for(future_recip_message, 60)
    delete_message = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete",
        }
    )
    get_messages = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/get",
        }
    )
    assert (
        delete_message["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/deleted"
    )
    assert get_messages["count"] == 0

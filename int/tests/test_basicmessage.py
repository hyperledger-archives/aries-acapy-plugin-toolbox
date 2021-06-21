"""Basic Message Tests"""
import asyncio
import pytest

from aries_staticagent import StaticConnection

@pytest.mark.asyncio
async def test_send(connection: StaticConnection, connection_id: str):
    with connection.next() as future_recip_message:
        sent_message = await asyncio.wait_for(
            connection.send_and_await_reply_async(
                {
                    "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                    "connection_id": connection_id,
                    "content": "Message #1: Your hovercraft is full of eels.",
                },
                return_route="all",
            ),
            timeout=60,
        )
        recip_message = await asyncio.wait_for(future_recip_message, 60)
    assert recip_message["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/sent"
    assert recip_message["message"]["content"] == "Message #1: Your hovercraft is full of eels."
    # Delete messages to clear the state between tests
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete",
        }
    )


@pytest.mark.asyncio
async def test_delete(connection: StaticConnection, connection_id: str):
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
    assert delete_message["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/deleted"
    assert get_messages["count"] == 0


@pytest.mark.asyncio
async def test_get(connection: StaticConnection, connection_id: str):
    with connection.next() as future_recip_message:
        sent_message = await asyncio.wait_for(
            connection.send_and_await_reply_async(
                {
                    "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                    "connection_id": connection_id,
                    "content": "Message #2: Are you suggesting coconuts migrate?",
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
                    "content": "Message #3: 'Tis but a flesh wound.",
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
    assert get_messages["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/messages"
    assert get_messages["count"] == 2
    # Delete messages to clear the state between tests
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete",
        }
    )


@pytest.mark.asyncio
async def test_get_limit_offset(connection: StaticConnection, connection_id: str):
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
            "offset": 2
        }
    )
    assert get_messages["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/messages"
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

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
                    "content": "Your hovercraft is full of eels.",
                },
                return_route="all",
            ),
            timeout=60,
        )
        recip_message = await asyncio.wait_for(future_recip_message, 60)

    assert recip_message
    assert sent_message

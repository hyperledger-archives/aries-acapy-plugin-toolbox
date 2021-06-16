"""Basic Message Tests"""
import pytest


@pytest.mark.asyncio
async def create_invitation(connection):
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True
        },
        return_route="all",
    )


@pytest.mark.asyncio
async def test_send(connection):
    await connection.send_and_await_reply(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
            "connection_id": "65dfdda3-2a64-4d9b-b8f1-106834f70a95",
            "content": "Your hovercraft is full of eels."
        }
    )
    reply = await connection.send_and_await_reply(
        {
	        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/get",
        }
    )
    print(reply)
    assert reply == "placeholder"
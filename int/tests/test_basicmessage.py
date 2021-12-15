"""Basic Message Tests"""
from aries_staticagent import Connection as StaticConnection, utils
from echo_agent import EchoClient
from echo_agent.models import ConnectionInfo
import pytest


@pytest.fixture
async def test_messages(echo, echo_connection, connection_id):
    async with echo.session(echo_connection) as session:
        for i in range(6):
            # This must be done by message or else the messages will not be recorded.
            # await send_basicmessage.asyncio(
            #     client=backchannel,
            #     conn_id=connection_id,
            #     json_body=SendMessage(content="Test Message #{}".format(i))
            # )

            # send_and_await_reply_async used instead of send_async to capture "sent"
            # message so it doesn't clog up echo agent's queue
            await echo.send_message_to_session(
                session,
                {
                    "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                    "connection_id": connection_id,
                    "content": "Test Message #{}".format(i),
                },
            )
            await echo.get_message(
                echo_connection,
                session=session,
                msg_type=(
                    "https://github.com/hyperledger/aries-toolbox/"
                    "tree/master/docs/admin-basicmessage/0.1/sent"
                ),
            )
        await echo.get_messages(echo_connection)


@pytest.fixture(autouse=True)
async def clear_messages(connection):
    yield
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete"
        },
        timeout=5,
    )


@pytest.mark.asyncio
async def test_send(
    connection_id: str, echo: EchoClient, echo_connection: ConnectionInfo
):
    """Test send message"""
    async with echo.session(echo_connection) as session:
        await echo.send_message_to_session(
            session,
            {
                "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                "connection_id": connection_id,
                "content": "Your hovercraft is full of eels.",
            },
        )
    sent_message = await echo.get_message(
        echo_connection,
        session=session,
        msg_type=(
            "https://github.com/hyperledger/aries-toolbox/"
            "tree/master/docs/admin-basicmessage/0.1/sent"
        ),
    )
    [recip_message] = await echo.get_messages(echo_connection)
    assert (
        recip_message["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/basicmessage/1.0/message"
    )
    assert recip_message["content"] == "Your hovercraft is full of eels."


@pytest.mark.asyncio
async def test_new(connection: StaticConnection):
    """Test new message notification"""
    # "new" message notifications are sent only over sessions.
    # This call must be done as a send_and_await_reply_async
    new_message = await connection.send_and_await_returned_async(
        {
            "@type": "https://didcomm.org/basicmessage/1.0/message",
            "~l10n": {"locale": "en"},
            "sent_time": utils.timestamp(),
            "content": "Your hovercraft is full of eels.",
        },
        timeout=10,
    )
    assert (
        new_message["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/new"
    )
    assert new_message["message"]["content"] == "Your hovercraft is full of eels."


@pytest.mark.asyncio
async def test_get(
    connection: StaticConnection, connection_id: str, echo, echo_connection
):
    """Send multiple messages and verify that the proper count and content appears in messages list"""
    test_content = ("Are you suggesting coconuts migrate?", "'Tis but a flesh wound.")
    for content in test_content:
        _ = await connection.send_and_await_returned_async(
            {
                "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/send",
                "connection_id": connection_id,
                "content": content,
            }
        )
    get_messages = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/get"
        }
    )
    await echo.get_messages(echo_connection)
    assert (
        get_messages["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/messages"
    )
    assert get_messages["count"] == 2
    assert get_messages["messages"][1]["content"] == test_content[0]
    assert get_messages["messages"][0]["content"] == test_content[1]


@pytest.mark.asyncio
async def test_get_limit_offset(
    connection: StaticConnection, connection_id: str, test_messages
):
    """Send multiple messages and verify that get returns the correct content according to the limit and offset"""
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


@pytest.mark.asyncio
async def test_delete(connection: StaticConnection, connection_id: str, test_messages):
    """Send multiple messages, delete them, and verify that the messages count is zero"""
    delete_message = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/delete"
        }
    )
    get_messages = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/get"
        }
    )
    assert (
        delete_message["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-basicmessage/0.1/deleted"
    )
    assert get_messages["count"] == 0

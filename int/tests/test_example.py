"""Example tests."""
import pytest


@pytest.mark.asyncio
async def test_empty_list(connection):
    reply = await connection.send_and_await_reply_async(
        {
	        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/get-list"
        },
        return_route="all",
    )
    assert len(reply["results"])-1 == 0


@pytest.mark.asyncio
async def test_create_invitation(connection):
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
    assert reply["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/invitation"


@pytest.mark.asyncio
async def test_get_list(connection):
    reply = await connection.send_and_await_reply_async(
        {
	        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/get-list"
        },
        return_route="all",
    )
    assert reply["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/list"



@pytest.mark.asyncio
async def test_num_results(connection):
    # Input number of messages to add to the list
    added_num = 3
    # Check current number of messages in the list
    check_list = await connection.send_and_await_reply_async(
        {
	        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/get-list"
        },
        return_route="all",
    )
    current_num = len(check_list["results"])-1
    # Add new messages
    for i in range(added_num):
        await connection.send_and_await_reply_async(
            {
                "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
                "alias": "Message I sent to Alice",
                "label": "Bob",
                "group": "admin",
                "auto_accept": True,
                "multi_use": True
            },
            return_route="all",
        )
    # Retrieve results of invitations list to verify that create message causes new item in results list
    reply = await connection.send_and_await_reply_async(
        {
	        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/get-list"
        },
        return_route="all",
    )
    assert len(reply["results"])-1 == current_num + added_num
"""Example tests."""
import pytest


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
            #"mediation_id": "42a1f1c9-b463-4f59-8385-2e2f7b70466a"
        },
        return_route="all",
    )
    assert reply["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/invitation"


@pytest.mark.asyncio
async def test_get_list_error(connection):
    reply = await connection.send_and_await_reply_async(
        {
	        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/invitation-get-list"
        },
        return_route="all",
    )
    assert reply["@type"] == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification/1.0/problem-report"


@pytest.mark.asyncio
async def test_get_list(connection):
    reply = await connection.send_and_await_reply_async(
        {
	        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/invitation-get-list"
        },
        return_route="all",
    )
    assert reply["@type"] == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/invitation-list"


@pytest.mark.asyncio
async def test_num_results(connection):
    # Create message
    await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
            "alias": "Invitation I sent to Alice",
            "label": "Bob",
            "group": "admin",
            "auto_accept": True,
            "multi_use": True,
            #"mediation_id": "42a1f1c9-b463-4f59-8385-2e2f7b70466a"
        },
        return_route="all",
    )
    # Retrieve invitations list
    reply = await connection.send_and_await_reply_async(
        {
	        "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/invitation-get-list"
        },
        return_route="all",
    )
    assert len(reply["results"]) == 2 # ??? need to verify that one has been added, not check the total number....

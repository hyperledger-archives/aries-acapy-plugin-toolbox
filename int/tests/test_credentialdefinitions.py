"""Credential Definition Tests"""
import asyncio
import pytest

from acapy_backchannel import Client
from acapy_backchannel.models.schema_send_request import SchemaSendRequest
from acapy_backchannel.api.schema import publish_schema


@pytest.fixture(scope="module")
async def create_schema(backchannel: Client, endorser_did):
    """Schema factory fixture"""

    async def _create_schema(version):
        return await publish_schema.asyncio(
            client=backchannel,
            json_body=SchemaSendRequest(
                attributes=["attr_1_0", "attr_1_1", "attr_1_2"],
                schema_name="Test Schema",
                schema_version=version,
            ),
        )

    yield _create_schema


@pytest.mark.asyncio
async def test_send_cred_def(connection, endorser_did, create_schema):
    """Create a credential definition"""
    schema = await create_schema(version="1.0")
    send_cred_def = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema.sent.schema_id,
            "~transport": {"return_route": "all"},
        },
        timeout=30,
    )
    assert (
        send_cred_def["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/credential-definition-id"
    )


@pytest.mark.asyncio
async def test_cred_def_get(connection, endorser_did, create_schema):
    """Create and retrieve a credential definition"""
    schema = await create_schema(version="1.1")
    send_cred_def = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema.sent.schema_id,
            "~transport": {"return_route": "all"},
        },
        timeout=30,
    )
    cred_def_get = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/credential-definition-get",
            "cred_def_id": send_cred_def["cred_def_id"],
            "~transport": {"return_route": "all"},
        }
    )
    assert (
        cred_def_get["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/credential-definition"
    )
    assert schema.sent.schema_id == cred_def_get["schema_id"]
    assert send_cred_def["cred_def_id"] == cred_def_get["cred_def_id"]


@pytest.mark.asyncio
async def test_cred_def_get_list(connection, endorser_did, create_schema):
    """Retrieve the list of credential definitions"""
    schema1_2 = await create_schema(version="1.2")
    send_schema1_2 = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema1_2.sent.schema_id,
            "~transport": {"return_route": "all"},
        },
        timeout=30,
    )
    schema1_3 = await create_schema(version="1.3")
    send_schema1_3 = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema1_3.sent.schema_id,
            "~transport": {"return_route": "all"},
        },
        timeout=30,
    )
    cred_def_get_list = await connection.send_and_await_reply_async(
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/credential-definition-get-list",
            "~transport": {"return_route": "all"},
        }
    )
    assert (
        cred_def_get_list["@type"]
        == "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1/credential-definition-list"
    )
    assert send_schema1_2["cred_def_id"] in [
        result["cred_def_id"] for result in cred_def_get_list["results"]
    ]
    assert send_schema1_3["cred_def_id"] in [
        result["cred_def_id"] for result in cred_def_get_list["results"]
    ]

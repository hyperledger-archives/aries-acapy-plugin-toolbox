"""Credential Definition Tests"""
import asyncio
import pytest


@pytest.fixture(scope="module")
async def create_schema(connection, endorser_did):
    """Schema factory fixture"""

    async def _create_schema():
        return await connection.send_and_await_reply_async(
            {
                "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/send-schema",
                "schema_name": "Test Schema",
                "schema_version": "1.0",
                "attributes": ["attr_1_0", "attr_1_1", "attr_1_2"],
                "return_route": "all",
            }
        )

    yield _create_schema


@pytest.mark.asyncio
async def test_send_cred_def(connection, endorser_did, create_schema):
    """Create a credential definition"""
    schema = await create_schema()
    send_cred_def = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema["schema_id"],
            "~transport": {"return_route": "all"},
        }
    )
    assert (
        send_cred_def["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/credential-definition-id"
    )


@pytest.mark.asyncio
async def test_cred_def_get(connection, endorser_did, create_schema):
    """Create and retrieve a credential definition"""
    schema = await create_schema()
    send_cred_def = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema["schema_id"],
            "~transport": {"return_route": "all"},
        }
    )
    cred_def_get = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/credential-definition-get",
            "cred_def_id": send_cred_def["cred_def_id"],
            "~transport": {"return_route": "all"},
        }
    )
    assert (
        cred_def_get["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/credential-definition"
    )


@pytest.mark.asyncio
async def test_cred_def_get_list(connection, endorser_did, create_schema):
    """Create and retrieve a credential definition"""
    schema1 = await create_schema()
    await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema1["schema_id"],
            "~transport": {"return_route": "all"},
        }
    )
    schema2 = await create_schema()
    await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema2["schema_id"],
            "~transport": {"return_route": "all"},
        }
    )
    cred_def_get_list = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/credential-definition-get-list",
            "~transport": {"return_route": "all"},
        }
    )
    assert (
        cred_def_get_list["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/credential-definition-list"
    )

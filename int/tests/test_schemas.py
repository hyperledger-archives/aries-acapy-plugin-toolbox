"""Schema Tests"""
import asyncio
import pytest
from aries_staticagent import MessageDeliveryError


@pytest.mark.asyncio
async def test_send_schema(connection, endorser_did):
    """Send a schema and verify message type"""
    schema = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/send-schema",
            "schema_name": "Test Schema",
            "schema_version": "1.0",
            "attributes": ["attr_1_0", "attr_1_1", "attr_1_2"],
            "return_route": "all",
        }
    )
    assert (
        schema["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/schema-id"
    )


@pytest.mark.asyncio
async def test_schema_get(connection, endorser_did):
    """Retrieve a pre-existing schema"""
    schema = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/send-schema",
            "schema_name": "Test Schema",
            "schema_version": "2.0",
            "attributes": ["attr_2_0", "attr_2_1", "attr_2_2"],
            "return_route": "all",
        },
        timeout=50,
    )
    schema_get = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/schema-get",
            "schema_id": schema["schema_id"],
            "@id": schema["@id"],
            "~transport": {"return_route": "all"},
        }
    )
    assert (
        schema_get["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/schema"
    )
    assert schema["schema_id"] == schema_get["schema_id"]
    assert schema["@id"] == schema_get["~thread"]["thid"]
    assert schema_get["author"] == "self"


@pytest.mark.asyncio
async def test_schema_get_list(connection, endorser_did):
    """Retrieve the list of schemas"""
    schema = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/send-schema",
            "schema_name": "Test Schema",
            "schema_version": "3.0",
            "attributes": ["attr_3_0", "attr_3_1", "attr_3_2"],
            "return_route": "all",
        },
        timeout=50,
    )
    schema_get_list = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/schema-get-list",
            "@id": schema["@id"],
            "~transport": {"return_route": "all"},
        }
    )
    assert (
        schema_get_list["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/schema-list"
    )
    assert schema["@id"] == schema_get_list["~thread"]["thid"]
    assert schema["schema_id"] in [
        result["schema_id"] for result in schema_get_list["results"]
    ]

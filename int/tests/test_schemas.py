"""Schema Tests"""
import asyncio
import pytest
from aries_staticagent import MessageDeliveryError


@pytest.mark.asyncio
async def test_send_schema(connection, make_endorser_did):
    """Send a schema and verify message type"""
    await make_endorser_did()
    try:
        schema = await connection.send_and_await_reply_async(
            {
                "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1/send-schema",
                "schema_name": "Test Schema",
                "schema_version": "1.0",
                "attributes": ["attr_0", "attr_1", "attr_2"],
                "return_route": "all",
            }
        )
    except MessageDeliveryError as error:
        print(error.msg)
    assert schema["schema_id"] == "UjF64u8jDEEuRve7PKQGUo:2:Alice's Test Schema:1.0"

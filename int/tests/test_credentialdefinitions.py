"""Credential Definition Tests"""
import asyncio
import pytest

from acapy_client import Client
from acapy_client.models.schema_send_request import SchemaSendRequest
from acapy_client.api.schema import publish_schema


@pytest.mark.asyncio
async def test_send_cred_def(connection, endorser_did, create_schema):
    """Create a credential definition"""
    schema = await create_schema(version="1.0")
    send_cred_def = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema.schema_id,
            "~transport": {"return_route": "all"},
        },
        timeout=50,
    )
    assert (
        send_cred_def["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/credential-definition-id"
    )


@pytest.mark.asyncio
async def test_cred_def_get(connection, endorser_did, create_schema):
    """Create and retrieve a credential definition"""
    schema = await create_schema(version="1.1")
    send_cred_def = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema.schema_id,
            "~transport": {"return_route": "all"},
        },
        timeout=50,
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
    assert schema.schema_id == cred_def_get["schema_id"]
    assert send_cred_def["cred_def_id"] == cred_def_get["cred_def_id"]


@pytest.mark.asyncio
async def test_cred_def_get_list(connection, endorser_did, create_schema):
    """Retrieve the list of credential definitions"""
    schema1_2 = await create_schema(version="1.2")
    send_schema1_2 = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema1_2.schema_id,
            "~transport": {"return_route": "all"},
        },
        timeout=50,
    )
    schema1_3 = await create_schema(version="1.3")
    send_schema1_3 = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1/send-credential-definition",
            "schema_id": schema1_3.schema_id,
            "~transport": {"return_route": "all"},
        },
        timeout=50,
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
    assert send_schema1_2["cred_def_id"] in [
        result["cred_def_id"] for result in cred_def_get_list["results"]
    ]
    assert send_schema1_3["cred_def_id"] in [
        result["cred_def_id"] for result in cred_def_get_list["results"]
    ]

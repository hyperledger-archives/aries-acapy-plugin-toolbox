"""Common fixtures for testing."""

import asyncio
import hashlib
import logging
import os
from typing import Iterator, Optional, Union

from acapy_client import Client
from acapy_client.api.connection import (
    create_static,
    delete_connection,
    set_metadata,
)
from acapy_client.api.credential_definition import publish_cred_def
from acapy_client.api.ledger import accept_taa, fetch_taa
from acapy_client.api.schema import publish_schema
from acapy_client.api.wallet import create_did, set_public_did
from acapy_client.models import (
    ConnectionMetadataSetRequest,
    ConnectionStaticRequest,
    ConnectionStaticResult,
    TAAAccept,
)
from acapy_client.models.conn_record import ConnRecord
from acapy_client.models.credential_definition_send_request import (
    CredentialDefinitionSendRequest,
)
from acapy_client.models.did import DID
from acapy_client.models.did_create import DIDCreate
from acapy_client.models.schema_send_request import SchemaSendRequest
from acapy_client.models.schema_send_result import SchemaSendResult
from aries_staticagent import Connection as StaticConnection, Target
from aries_staticagent.message import Message
from echo_agent import EchoClient
from echo_agent.models import ConnectionInfo
import httpx
import pytest

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create a session scoped event loop.
    pytest.asyncio plugin provides a default function scoped event loop
    which cannot be used as a dependency to session scoped fixtures.
    """
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
def host():
    """Hostname of agent under test."""
    return os.environ.get("AGENT_HOST", "localhost")


@pytest.fixture(scope="session")
def suite_host():
    """Hostname of agent under test."""
    return os.environ.get("SUITE_HOST", "localhost")


@pytest.fixture(scope="session")
def port():
    """Port of agent under test."""
    return os.environ.get("AGENT_PORT", 3000)


@pytest.fixture(scope="session")
def suite_port():
    """Port of agent under test."""
    return os.environ.get("SUITE_PORT", 3002)


@pytest.fixture(scope="session")
def backchannel_port():
    """Port of agent under test backchannel."""
    return os.environ.get("AGENT_BACKCHANNEL_PORT", 3001)


@pytest.fixture(scope="session")
def backchannel(host, backchannel_port):
    """Yield backchannel client."""
    yield Client(base_url="http://{}:{}".format(host, backchannel_port))


@pytest.fixture(scope="session")
def suite_seed():
    yield hashlib.sha256(b"acapy-plugin-toolbox-int-test-runner").hexdigest()[:32]


@pytest.fixture(scope="session")
def agent_seed():
    yield hashlib.sha256(b"acapy-plugin-toolbox-int-test-runner").hexdigest()[:32]


@pytest.fixture(scope="session")
def suite_endpoint():
    yield os.environ.get("SUITE_ENDPOINT", "http://localhost:3000")


@pytest.fixture(scope="session")
def agent_endpoint(host, port):
    yield "http://{}:{}".format(host, port)


@pytest.fixture(scope="session")
def agent_connection(
    suite_seed, agent_seed, suite_endpoint, backchannel
) -> Iterator[ConnectionStaticResult]:
    """Yield agent's representation of this connection."""

    # Create connection in agent under test
    create_result: Optional[ConnectionStaticResult] = create_static.sync(
        client=backchannel,
        json_body=ConnectionStaticRequest.from_dict(
            {
                "my_seed": agent_seed,
                "their_seed": suite_seed,
                "their_endpoint": suite_endpoint,
                "their_label": "test-runner",
            }
        ),
    )
    if not create_result:
        raise RuntimeError("Could not create static connection with agent under test")

    # Set admin metadata to enable access to admin protocols
    set_result = set_metadata.sync(
        client=backchannel,
        conn_id=create_result.record.connection_id,
        json_body=ConnectionMetadataSetRequest.from_dict(
            {"metadata": {"group": "admin"}}
        ),
    )
    if not set_result:
        raise RuntimeError("Could not set metadata on static connection")

    yield create_result

    delete_connection.sync(
        client=backchannel, conn_id=create_result.record.connection_id
    )


@pytest.fixture(scope="session")
def conn_record(agent_connection: ConnectionStaticResult):
    yield agent_connection.record


@pytest.fixture(scope="session")
def connection_id(conn_record: ConnRecord):
    yield conn_record.connection_id


class IntegrationTestConnection(StaticConnection):
    async def send_and_await_reply_async(
        self,
        msg: Union[dict, Message],
        *,
        return_route: str = "all",
        plaintext: bool = False,
        anoncrypt: bool = False,
        timeout: int = 1,
    ) -> Message:
        return await super().send_and_await_reply_async(
            msg,
            return_route=return_route,
            plaintext=plaintext,
            anoncrypt=anoncrypt,
            timeout=timeout,
        )


@pytest.fixture(scope="session")
def connection(agent_connection: ConnectionStaticResult, suite_seed: str):
    """Yield static connection to agent under test."""

    # Create and yield static connection
    yield IntegrationTestConnection.from_seed(
        seed=suite_seed.encode("ascii"),
        target=Target(
            endpoint=agent_connection.my_endpoint, their_vk=agent_connection.my_verkey
        ),
    )


@pytest.fixture(scope="session")
def echo_agent(suite_host, suite_port):
    yield EchoClient(base_url=f"http://{suite_host}:{suite_port}")


@pytest.fixture
async def echo(echo_agent: EchoClient):
    async with echo_agent:
        yield echo_agent


@pytest.fixture(scope="session")
async def echo_connection(echo_agent: EchoClient, suite_seed, agent_connection):
    async with echo_agent:
        conn = await echo_agent.new_connection(
            seed=suite_seed,
            endpoint=agent_connection.my_endpoint,
            their_vk=agent_connection.my_verkey,
        )
    yield conn
    async with echo_agent:
        await echo_agent.delete_connection(conn)


@pytest.fixture(scope="session")
def asynchronously_received_messages(
    echo_agent: EchoClient, echo_connection: ConnectionInfo
):
    """Get asynchronously recevied messages from the echo agent."""
    # Could wipe left over messages here
    async def _asynchronously_received_messages():
        async with echo_agent as echo:
            messages = await echo.get_messages(echo_connection)
        return messages

    yield _asynchronously_received_messages
    # Could wipe remaining messages here


@pytest.fixture(scope="session")
def wait_for_message(echo_agent: EchoClient, echo_connection: ConnectionInfo):
    """Get asynchronously recevied messages from the echo agent."""
    # Could wipe left over messages here
    async def _wait_for_message(
        *, thid: Optional[str] = None, msg_type: Optional[str] = None, timeout: int = 5
    ):
        async with echo_agent as echo:
            assert echo.client
            echo.client.timeout = timeout + 1
            return await echo.get_message(
                echo_connection, thid=thid, msg_type=msg_type, timeout=timeout
            )

    yield _wait_for_message
    # Could wipe remaining messages here


@pytest.fixture(scope="session")
def send_via_echo(echo_agent, echo_connection: ConnectionInfo):
    async def _send_via_echo(message: dict):
        async with echo_agent as echo:
            await echo.send_message(echo_connection, message)

    yield _send_via_echo


@pytest.fixture(scope="session")
async def make_did(backchannel):
    """DID factory fixture"""

    async def _make_did():
        return (
            await create_did.asyncio(
                client=backchannel.with_timeout(15), json_body=DIDCreate()
            )
        ).result

    yield _make_did
    # TODO create DID deletion method


@pytest.fixture(scope="session")
async def accepted_taa(backchannel):
    result = (await fetch_taa.asyncio(client=backchannel.with_timeout(15))).result
    result = await accept_taa.asyncio(
        client=backchannel,
        json_body=TAAAccept(
            mechanism="on_file",
            text=result.taa_record.text,
            version=result.taa_record.version,
        ),
    )


@pytest.fixture(scope="session")
async def endorser_did(make_did, backchannel, accepted_taa):
    """Endorser DID factory fixture"""
    did: DID = await make_did()
    LOGGER.info("Publishing DID through https://selfserve.indiciotech.io")
    try:
        response = httpx.post(
            url="https://selfserve.indiciotech.io/nym",
            json={"network": "testnet", "did": did.did, "verkey": did.verkey},
            timeout=15,
        )
    except httpx.ReadTimeout as err:
        raise Exception("Failed to publish DID: {0}".format(err))
    if response.is_error:
        raise Exception("Failed to publish DID:", response.text)

    LOGGER.info("DID Published")
    result = await set_public_did.asyncio_detailed(
        client=backchannel.with_timeout(15), did=did.did
    )
    assert result.status_code == 200
    yield did


@pytest.fixture(scope="module")
async def create_schema(backchannel: Client, endorser_did):
    """Schema factory fixture."""

    async def _create_schema(version):
        return await publish_schema.asyncio(
            client=backchannel.with_timeout(60),
            json_body=SchemaSendRequest(
                attributes=["attr_1_0", "attr_1_1", "attr_1_2"],
                schema_name="Test Schema",
                schema_version=version,
            ),
        )

    yield _create_schema


@pytest.fixture(scope="module")
async def create_cred_def(backchannel: Client, endorser_did, create_schema):
    """Credential definition fixture."""

    async def _create_cred_def(version):
        schema = await create_schema(version)
        assert isinstance(schema, SchemaSendResult)
        return await publish_cred_def.asyncio(
            client=backchannel.with_timeout(60),
            json_body=CredentialDefinitionSendRequest(schema_id=schema.schema_id),
        )

    yield _create_cred_def

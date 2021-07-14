"""Common fixtures for testing."""

import asyncio
from contextlib import suppress
import os
import base64
from typing import Iterator, Optional
from acapy_backchannel.models.conn_record import ConnRecord
from acapy_backchannel.models.did import DID
import pytest
import hashlib
import httpx

from acapy_backchannel import Client
from acapy_backchannel.api.connection import (
    create_static,
    set_metadata,
    delete_connection,
)
from acapy_backchannel.api.wallet import (
    create_did,
    set_public_did,
)
from acapy_backchannel.api.ledger import accept_taa, fetch_taa
from acapy_backchannel.models import (
    ConnectionStaticRequest,
    ConnectionStaticResult,
    ConnectionMetadataSetRequest,
    TAAAccept,
)

from aries_staticagent import StaticConnection, Target

from . import BaseAgent

import logging

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
def suite_endpoint(suite_host, suite_port):
    yield "http://{}:{}".format(suite_host, suite_port)


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


@pytest.fixture(scope="session")
def connection(agent_connection: ConnectionStaticResult, suite_seed: str):
    """Yield static connection to agent under test."""
    # Create and yield static connection
    yield StaticConnection.from_seed(
        seed=suite_seed.encode("ascii"),
        target=Target(
            endpoint=agent_connection.my_endpoint, their_vk=agent_connection.my_verkey
        ),
    )


@pytest.fixture(scope="session")
def agent(suite_host, suite_port, connection: StaticConnection):
    yield BaseAgent(suite_host, suite_port, connection)


@pytest.fixture(scope="session", autouse=True)
async def http_endpoint(agent: BaseAgent):
    """Start up http endpoint for suite."""
    server_task = asyncio.ensure_future(agent.start_async())

    yield

    server_task.cancel()
    with suppress(asyncio.CancelledError):
        await server_task
    await agent.cleanup()


@pytest.fixture
async def make_did(backchannel):
    """DID factory fixture"""

    async def _make_did():
        return (await create_did.asyncio(client=backchannel)).result

    yield _make_did
    # TODO create DID deletion method


@pytest.fixture(scope="session")
async def accepted_taa(backchannel):
    result = (await fetch_taa.asyncio(client=backchannel)).result
    result = await accept_taa.asyncio(
        client=backchannel,
        json_body=TAAAccept(
            mechanism="on_file",
            text=result.taa_record.text,
            version=result.taa_record.version,
        ),
    )


@pytest.fixture
async def make_endorser_did(make_did, backchannel, accepted_taa):
    """Endorser DID factory fixture"""

    async def _make_endorser_did():
        did: DID = await make_did()
        LOGGER.info("Publishing DID through https://selfserve.indiciotech.io")
        response = httpx.post(
            url="https://selfserve.indiciotech.io/nym",
            json={
                "network": "testnet",
                "did": did.did,
                "verkey": did.verkey,
            },
        )
        if response.is_error:
            raise Exception("Failed to publish DID:", response.text)

        LOGGER.info("DID Published")
        result = await set_public_did.asyncio_detailed(
            client=backchannel,
            did=did.did,
        )
        assert result.status_code == 200
        return did

    yield _make_endorser_did

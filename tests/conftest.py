"""Common testing fixtures."""
from contextlib import contextmanager
import pytest
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.in_memory import InMemoryProfile
from aries_cloudagent.messaging.request_context import RequestContext
from aries_cloudagent.messaging.responder import MockResponder
from asynctest import mock


@pytest.fixture
def mock_admin_connection():
    """Mock connection fixture."""
    connection = mock.MagicMock(spec=ConnRecord)
    connection.metadata_get = mock.CoroutineMock(return_value="admin")
    yield connection


@pytest.fixture
def profile():
    """Profile fixture."""
    yield InMemoryProfile.test_profile()


@pytest.fixture
def context(profile, mock_admin_connection):
    """RequestContext fixture."""
    context = RequestContext(profile)
    context.connection_record = mock_admin_connection
    context.connection_ready = True
    yield context


@pytest.fixture
def mock_responder():
    """Mock responder fixture."""
    yield MockResponder()


@contextmanager
def mock_get_connection(module, conn: ConnRecord = None):
    """Mock get_connection on a module"""
    with mock.patch.object(
        module,
        "get_connection",
        mock.CoroutineMock(return_value=conn or mock.MagicMock(spec=ConnRecord))
    ) as get_connection:
        yield get_connection

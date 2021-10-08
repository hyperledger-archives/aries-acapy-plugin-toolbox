"""Test CredGetList message and handler."""
import pytest
from acapy_plugin_toolbox.holder import v0_1 as test_module
from acapy_plugin_toolbox.holder.v0_1 import CredGetList, CredList
from acapy_plugin_toolbox.decorators.pagination import Paginate
from contextlib import contextmanager
from asynctest import mock


@pytest.fixture
def cred_record():
    """Factory for test credential records."""

    def _cred_record():
        return test_module.CredExRecord()

    yield _cred_record


@pytest.fixture
def message():
    """Message fixture."""
    paginate = Paginate()
    yield CredGetList(paginate=paginate)


@pytest.fixture
def context(context, message):
    """Context fixture."""
    context.message = message
    yield context


@pytest.fixture
def mock_record_query():
    """Mock CredExRecord.query on a module."""

    @contextmanager
    def _mock_record_query(obj, result=None, spec=None):
        with mock.patch.object(
            obj,
            "query",
            mock.CoroutineMock(return_value=result or mock.MagicMock(spec=spec)),
        ) as record_query:
            yield record_query

    yield _mock_record_query


@pytest.mark.asyncio
async def test_handler(
    context, mock_responder, message, mock_record_query, cred_record
):
    """Test CredGetList handler."""
    rec1 = cred_record()
    with mock_record_query(
        test_module.CredExRecord, [rec1], spec=test_module.CredExRecord
    ) as record_query:
        await message.handle(context, mock_responder)
    record_query.assert_called_once()
    assert len(mock_responder.messages) == 1
    cred_list, _ = mock_responder.messages[0]
    assert isinstance(cred_list, CredList)
    assert cred_list.serialize()
    assert cred_list.results == [rec1.serialize()]
    assert cred_list.page is not None
    assert cred_list.page.count == 1

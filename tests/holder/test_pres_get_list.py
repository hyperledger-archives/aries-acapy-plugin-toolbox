"""Test PresGetList message and handler."""
import pytest
from acapy_plugin_toolbox.holder import v0_1 as test_module
from acapy_plugin_toolbox.holder.v0_1 import PresGetList, PresList

TEST_CONN_ID = "test-connection-id"


@pytest.fixture
def pres_record():
    """Factory for test presentation records."""

    def _pres_record():
        return test_module.PresExRecord()

    yield _pres_record


@pytest.fixture
def message():
    """Message fixture."""
    yield PresGetList(connection_id=TEST_CONN_ID)


@pytest.fixture
def context(context, message):
    """Context fixture."""
    context.message = message
    yield context


@pytest.mark.asyncio
async def test_handler(
    context, mock_responder, message, mock_record_query, pres_record
):
    """Test PresGetList handler."""
    rec1 = pres_record()
    with mock_record_query(
        test_module.PresExRecord, [rec1], spec=test_module.PresExRecord
    ) as record_query:
        await message.handle(context, mock_responder)
    record_query.assert_called_once()
    assert len(mock_responder.messages) == 1
    pres_list, _ = mock_responder.messages[0]
    assert isinstance(pres_list, PresList)
    assert pres_list.serialize()
    assert pres_list.results == [rec1.serialize()]
    assert pres_list.page is not None
    assert pres_list.page.count == 1

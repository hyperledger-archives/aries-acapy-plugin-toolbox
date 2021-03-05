"""Common fixtures for holder protocol."""

from contextlib import contextmanager

import pytest
from asynctest import mock


@pytest.fixture
def mock_record_query():
    """Mock PresExRecord.query on a module."""
    @contextmanager
    def _mock_record_query(obj, result=None, spec=None):
        with mock.patch.object(
            obj, "query",
            mock.CoroutineMock(
                return_value=result or
                mock.MagicMock(spec=spec)
            )
        ) as record_query:
            yield record_query
    yield _mock_record_query

"""Common fixtures for holder protocol."""

from contextlib import contextmanager

import pytest
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from asynctest import mock


@pytest.fixture
def mock_record_query():
    """Mock PresExRecord.query on a module."""

    @contextmanager
    def _mock_record_query(obj, result=None, spec=None):
        with mock.patch.object(
            obj,
            "query",
            mock.CoroutineMock(return_value=result or mock.MagicMock(spec=spec)),
        ) as record_query:
            yield record_query

    yield _mock_record_query


@pytest.fixture
def mock_get_pres_ex_record():
    """Mock get_pres_ex_record."""

    @contextmanager
    def _mock_get_pres_ex_record(obj, pres_ex_record: PresExRecord = None):
        with mock.patch.object(
            obj,
            "get_pres_ex_record",
            mock.CoroutineMock(
                return_value=pres_ex_record or mock.MagicMock(autospec=True)
            ),
        ) as get_pres_ex_record:
            yield get_pres_ex_record

    yield _mock_get_pres_ex_record

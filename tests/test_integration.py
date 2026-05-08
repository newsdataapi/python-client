"""Live API integration tests for newsdataapi.

These tests hit the actual NewsData.io API. They require a valid API key
in the ``PYTEST_TOKEN`` environment variable and consume API quota on
every run.

By default they are skipped (the ``integration`` marker is filtered out
by ``addopts`` in ``pyproject.toml``). Opt in with::

    pytest -m integration
    pytest -m ""              # to run everything

If ``PYTEST_TOKEN`` is not set when integration tests are explicitly
requested, every test in this module is skipped.
"""

from __future__ import annotations

import datetime
import os
from collections.abc import Iterator

import pytest

from newsdataapi import NewsDataApiClient

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def api() -> Iterator[NewsDataApiClient]:
    key = os.environ.get("PYTEST_TOKEN")
    if not key:
        pytest.skip("PYTEST_TOKEN not set; skipping live API tests")
    with NewsDataApiClient(key) as client:
        yield client


def _last_30_days() -> tuple[str, str]:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    fmt = "%Y-%m-%d 00:00:00"
    return (now - datetime.timedelta(days=30)).strftime(fmt), now.strftime(fmt)


def test_latest_api(api: NewsDataApiClient) -> None:
    response = api.latest_api()
    assert isinstance(response, dict)
    assert response["status"] == "success"


def test_archive_api(api: NewsDataApiClient) -> None:
    response = api.archive_api(q="news")
    assert isinstance(response, dict)
    assert response["status"] == "success"


def test_sources_api(api: NewsDataApiClient) -> None:
    response = api.sources_api()
    assert isinstance(response, dict)
    assert response["status"] == "success"


def test_crypto_api(api: NewsDataApiClient) -> None:
    response = api.crypto_api(q="bitcoin")
    assert isinstance(response, dict)
    assert response["status"] == "success"


def test_market_api(api: NewsDataApiClient) -> None:
    response = api.market_api()
    assert isinstance(response, dict)
    assert response["status"] == "success"


def test_count_api(api: NewsDataApiClient) -> None:
    from_date, to_date = _last_30_days()
    response = api.count_api(
        from_date=from_date,
        to_date=to_date,
        language="en",
    )
    assert isinstance(response, dict)
    assert response["status"] == "success"


def test_crypto_count_api(api: NewsDataApiClient) -> None:
    from_date, to_date = _last_30_days()
    response = api.crypto_count_api(
        from_date=from_date,
        to_date=to_date,
        language="en",
    )
    assert isinstance(response, dict)
    assert response["status"] == "success"


def test_market_count_api(api: NewsDataApiClient) -> None:
    from_date, to_date = _last_30_days()
    response = api.market_count_api(
        from_date=from_date,
        to_date=to_date,
        language="en",
    )
    assert isinstance(response, dict)
    assert response["status"] == "success"

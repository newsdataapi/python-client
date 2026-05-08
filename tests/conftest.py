"""Shared pytest fixtures for the newsdataapi test suite."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import responses

from newsdataapi import NewsDataApiClient


@pytest.fixture
def mocked_responses() -> Iterator[responses.RequestsMock]:
    """Intercept all HTTP traffic for the duration of one test.

    Tests register expected responses on the yielded ``RequestsMock``;
    requests that don't match a registered response raise ``ConnectionError``.
    """
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def client() -> Iterator[NewsDataApiClient]:
    """A :class:`NewsDataApiClient` with retry timing tuned for tests.

    The default ``retry_backoff=2.0`` and ``retry_backoff_max=60.0`` would
    make the retry-path tests sleep for tens of seconds. Pair this fixture
    with :func:`no_sleep` to remove the residual sleeps entirely.
    """
    with NewsDataApiClient(
        "test_key_xxx",
        max_retries=3,
        retry_backoff=0.001,
        retry_backoff_max=0.01,
        pagination_delay=0.0,
        request_timeout=5.0,
    ) as c:
        yield c


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace :func:`time.sleep` (as imported by the client) with a no-op."""
    monkeypatch.setattr(
        "newsdataapi.client.time.sleep",
        lambda *_args, **_kwargs: None,
    )

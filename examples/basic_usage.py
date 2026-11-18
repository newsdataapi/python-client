"""Basic usage example for the newsdataapi SDK.

Run with::

    NEWSDATA_API_KEY=<your-api-key> python examples/basic_usage.py

The example exercises the four most common patterns:

1. A single request (the default).
2. Pagination via ``paginate=True`` (a generator of per-page responses).
3. Auto-merge via ``scroll=True`` (one merged response).
4. Persisting results to CSV.

It also shows the typed exception hierarchy in :func:`example_error_handling`.
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path

from newsdataapi import (
    NewsDataApiClient,
    NewsdataAPIError,
    NewsdataAuthError,
    NewsdataRateLimitError,
)


def main() -> None:
    apikey = os.environ.get("NEWSDATA_API_KEY")
    if not apikey:
        raise SystemExit(
            "Set NEWSDATA_API_KEY in your environment "
            "before running this example."
        )

    out_dir = Path.cwd() / "news_csv"
    out_dir.mkdir(exist_ok=True)

    # The context manager closes the underlying HTTP session cleanly when
    # the block exits. You can also call ``client.close()`` yourself.
    with NewsDataApiClient(apikey, folder_path=out_dir) as client:
        # 1. Single request — the most common pattern.
        response = client.news(q="bitcoin", country="us", language="en")
        results = response["results"]
        print(
            f"news: {len(results)} articles, "
            f"total available: {response.get('total_results')}"
        )

        # 2. Pagination — yields one response per page, capped at max_pages.
        for page_index, page in enumerate(
            client.crypto(q="ethereum", paginate=True, max_pages=3),
            start=1,
        ):
            print(f"  crypto page {page_index}: {len(page['results'])} articles")

        # 3. Scroll — auto-follows next_page cursors and merges into one dict.
        # ``from_date`` / ``to_date`` select historical news.
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        date_format = "%Y-%m-%d 00:00:00"
        merged = client.news(
            q="apple",
            from_date=(now - datetime.timedelta(days=7)).strftime(date_format),
            to_date=(now - datetime.timedelta(days=1)).strftime(date_format),
            scroll=True,
            max_result=50,
        )
        print(f"scrolled news: {len(merged['results'])} articles")

        # 4. Persist results to CSV. ``folder_path`` was set on the client, so
        # we don't pass it again here.
        path = client.save_to_csv(response, filename="bitcoin")
        print(f"wrote {path}")


def example_error_handling(apikey: str) -> None:
    """Selectively handle different failure modes.

    The exception hierarchy lets you react differently to each kind of
    failure. Catching :class:`NewsdataException` (the base) is always a
    valid catch-all.
    """
    with NewsDataApiClient(apikey) as client:
        try:
            client.news(q="news")
        except NewsdataAuthError as e:
            print(f"API key rejected (HTTP {e.status_code})")
        except NewsdataRateLimitError as e:
            print(f"rate limited; retry after {e.retry_after}s")
        except NewsdataAPIError as e:
            print(f"API error {e.status_code}: {e.response_body}")


if __name__ == "__main__":
    main()

<div align="center">

[![NewsData.io logo](https://raw.githubusercontent.com/bytesview/python-client/main/newsdata-logo.png)](https://newsdata.io)

# NewsData.io Python Client

[![Build Status](https://img.shields.io/github/actions/workflow/status/bytesview/python-client/ci.yml)](https://github.com/bytesview/python-client/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/bytesview/python-client/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/newsdataapi?color=084298)](https://pypi.org/project/newsdataapi)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/newsdataapi)](https://pypi.org/project/newsdataapi)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/newsdataapi)](https://pypi.org/project/newsdataapi)

</div>

`newsdataapi` is the official Python SDK for the [NewsData.io](https://newsdata.io) REST API. It wraps every endpoint (`latest`, `archive`, `sources`, `crypto`, `market`, `count`, `crypto/count`, `market/count`) with consistent retry, pagination, and error handling.

## Installation

```bash
pip install newsdataapi
```

If you use [uv](https://github.com/astral-sh/uv):

```bash
uv add newsdataapi
```

Supports Python 3.8 through 3.14. The only runtime dependency is `requests`.

## Quickstart

```python
from newsdataapi import NewsDataApiClient

with NewsDataApiClient("YOUR_API_KEY") as client:
    response = client.latest_api(q="bitcoin", country="us", language="en")
    for article in response["results"]:
        print(article["title"], "-", article["link"])
```

The context-manager form closes the underlying HTTP session cleanly when the block exits. If you prefer not to use `with`, create the client directly and call `client.close()` yourself:

```python
from newsdataapi import NewsDataApiClient

client = NewsDataApiClient("YOUR_API_KEY")
try:
    response = client.latest_api(q="bitcoin", country="us", language="en")
    for article in response["results"]:
        print(article["title"], "-", article["link"])
finally:
    client.close()
```

## Endpoints

| Method | Endpoint | Notes |
|--------|----------|-------|
| `latest_api()` | `/latest` | Real-time news |
| `archive_api()` | `/archive` | Historical news |
| `sources_api()` | `/sources` | Available news sources |
| `crypto_api()` | `/crypto` | Cryptocurrency news |
| `market_api()` | `/market` | Market / financial news |
| `count_api(from_date, to_date)` | `/count` | Aggregate counts |
| `crypto_count_api(from_date, to_date)` | `/crypto/count` | Aggregate crypto counts |
| `market_count_api(from_date, to_date)` | `/market/count` | Aggregate market counts |

All endpoint parameters are keyword-only (except the required `from_date` / `to_date` on the count endpoints). Most accept either a single string or a `list[str]`; lists are comma-joined for the API.

See the [NewsData.io documentation](https://newsdata.io/documentation) for the full parameter reference.

## Three ways to consume an endpoint

```python
# 1. Single request (the default).
response = client.latest_api(q="news")

# 2. Auto-merge — follow nextPage cursors and return one combined dict.
merged = client.latest_api(q="news", scroll=True, max_result=200)

# 3. Iterate one response per page (a generator).
for page in client.latest_api(q="news", paginate=True, max_pages=5):
    process(page["results"])
```

`scroll` and `paginate` are mutually exclusive. `scroll=True` truncates strictly to `max_result`; `paginate=True` stops at `max_pages` or when the API returns no `nextPage`.

## Error handling

```python
from newsdataapi import (
    NewsdataAPIError,
    NewsdataAuthError,
    NewsdataNetworkError,
    NewsdataRateLimitError,
)

try:
    client.latest_api(q="news")
except NewsdataAuthError as e:
    print(f"bad API key (HTTP {e.status_code})")
except NewsdataRateLimitError as e:
    print(f"rate limited; retry after {e.retry_after}s")
except NewsdataAPIError as e:
    print(f"API error {e.status_code}: {e.response_body}")
except NewsdataNetworkError as e:
    print(f"network failure: {e.original}")
```

The full hierarchy:

```
NewsdataException
├── NewsdataValidationError      (also a ValueError; carries .param)
├── NewsdataAPIError             (carries .status_code, .response_body)
│   ├── NewsdataAuthError        (401 / 403)
│   ├── NewsdataRateLimitError   (429; carries .retry_after)
│   └── NewsdataServerError      (5xx)
└── NewsdataNetworkError         (carries .original)
```

`NewsdataException` is always a valid catch-all.

## Save results to CSV

```python
client.save_to_csv(response, folder_path="./out", filename="latest_news")

# Or set folder_path once on the client and reuse:
client = NewsDataApiClient(apikey, folder_path="./out")
client.save_to_csv(response, filename="latest_news")
```

`save_to_csv` returns a `pathlib.Path`. Cell values that are dicts or lists are stringified (`key:value,key:value` for dicts, comma-joined for lists). Quoting is delegated to the standard `csv.DictWriter`, so the output round-trips correctly through any CSV reader.

The function is also importable as a standalone:

```python
from newsdataapi import save_to_csv
save_to_csv(response, folder_path="./out", filename="latest_news")
```

## Configuration

```python
client = NewsDataApiClient(
    apikey="...",
    request_timeout=30,         # seconds; default 30
    max_retries=5,              # default 5
    retry_backoff=2.0,          # base seconds, exponential; default 2.0
    retry_backoff_max=60.0,     # cap on a single retry sleep; default 60.0
    pagination_delay=1.0,       # seconds between pages; default 1.0
    max_result=None,            # cap on merged results in scroll mode; default None (no cap)
    max_pages=None,             # cap on pages yielded in paginate mode; default None (no cap)
    proxies={"https": "..."},   # passed to requests.Session.get
    accept_language="en",       # Accept-Language header
    include_headers=False,      # if True, returned dicts include response_headers
    base_url="...",             # override for staging / proxied environments
    session=my_session,         # inject your own requests.Session
    folder_path="./out",        # default folder for save_to_csv; default None
)
```

Defaults sleep about a minute total across all retries (2 s → 4 s → 8 s → 16 s → 32 s, capped at 60 s); 429 responses honor `Retry-After` (both integer-seconds and HTTP-date forms are parsed). The API key is redacted in log output.

## Development

This project uses [uv](https://github.com/astral-sh/uv) for environment and lock management.

```bash
git clone https://github.com/bytesview/python-client
cd python-client
uv sync                                # creates .venv, installs runtime + dev deps from uv.lock
```

Run the suite:

```bash
uv run pytest                                         # unit tests only (default)
PYTEST_TOKEN=<api-key> uv run pytest -m integration   # live-API tests
PYTEST_TOKEN=<api-key> uv run pytest -m ""            # all tests

uv run ruff check src/ tests/ examples/
uv run mypy src/
```

Dev dependencies live in PEP 735 `[dependency-groups].dev` (uv-native). Plain `pip install -e ".[dev]"` will not pick them up; if you can't use uv, install the contents of the `dev` group in `pyproject.toml` by hand.

## License

MIT. See the [LICENSE](LICENSE) file.

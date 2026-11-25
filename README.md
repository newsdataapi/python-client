<div align="center">

[![NewsData.io logo](https://raw.githubusercontent.com/newsdataapi/python-client/main/newsdata-logo.png)](https://newsdata.io)

# NewsData.io Python Client

[![Build Status](https://img.shields.io/github/actions/workflow/status/newsdataapi/python-client/ci.yml)](https://github.com/newsdataapi/python-client/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/newsdataapi/python-client/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/newsdataapi?color=084298)](https://pypi.org/project/newsdataapi)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/newsdataapi)](https://pypi.org/project/newsdataapi)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/newsdataapi)](https://pypi.org/project/newsdataapi)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-85EA2D)](https://newsdata.io/openapi.json)

</div>

`newsdataapi` is the official Python SDK for the [NewsData.io](https://newsdata.io) REST API. It wraps every endpoint of both API versions, version 2 (`news`, `market`, `crypto`, `sources`, `count/news`, `count/market`, `count/crypto`) and version 1 (`latest`, `archive`, `crypto`, `market`, `sources`, `count`, `crypto/count`, `market/count`), with consistent retry, pagination, and error handling. It also covers the real-time WebSocket service end to end with `NewsDataApiWebSocket`: register, list, and delete queries, and stream the matching news as it is published (sync or asyncio).

## Installation

```bash
pip install newsdataapi
```

If you use [uv](https://github.com/astral-sh/uv):

```bash
uv add newsdataapi
```

Supports Python 3.8 through 3.14. The runtime dependencies are `requests` (REST) and `websockets` (real-time streaming). `NewsDataApiWebSocket` requires Python 3.10 or newer, so `websockets` is only installed there; on 3.8 and 3.9 the REST client works as usual.

## Quickstart

```python
from newsdataapi import NewsDataApiClient

with NewsDataApiClient("YOUR_API_KEY") as client:
    response = client.news(q="bitcoin", country="us", language="en")
    for article in response["results"]:
        print(article["title"], "-", article["url"])
```

The context-manager form closes the underlying HTTP session cleanly when the block exits. If you prefer not to use `with`, create the client directly and call `client.close()` yourself:

```python
from newsdataapi import NewsDataApiClient

client = NewsDataApiClient("YOUR_API_KEY")
try:
    response = client.news(q="bitcoin", country="us", language="en")
    for article in response["results"]:
        print(article["title"], "-", article["url"])
finally:
    client.close()
```

The version 1 methods are called the same way, for example `client.latest_api(q="bitcoin", country="us", language="en")`; their articles use the version 1 layout, with `link` instead of `url` (see "Version 1 and version 2" below).

## Endpoints

Both API versions are available, and the client has methods for each.

### API version 2

| Method | Endpoint | Notes |
|--------|----------|-------|
| `news()` | `/2/news` | Latest news, or historical news with `from_date` / `to_date` |
| `market()` | `/2/market` | Market / financial news |
| `crypto()` | `/2/crypto` | Cryptocurrency news |
| `sources()` | `/2/sources` | Available news sources |
| `count_news()` | `/2/count/news` | News counts per time interval |
| `count_market()` | `/2/count/market` | Market news counts per time interval |
| `count_crypto()` | `/2/count/crypto` | Crypto news counts per time interval |

The version 2 count methods return `total_results` and a `results` list with one `{"date_time": ..., "count": ...}` entry per `interval` (`month`, `day` or `hour`). They page like the news methods, so `scroll` and `paginate` work on them too.

### API version 1

| Method | Endpoint | Notes |
|--------|----------|-------|
| `latest_api()` | `/1/latest` | Real-time news |
| `archive_api()` | `/1/archive` | Historical news |
| `sources_api()` | `/1/sources` | Available news sources |
| `crypto_api()` | `/1/crypto` | Cryptocurrency news |
| `market_api()` | `/1/market` | Market / financial news |
| `count_api(from_date, to_date)` | `/1/count` | Aggregate counts |
| `crypto_count_api(from_date, to_date)` | `/1/crypto/count` | Aggregate crypto counts |
| `market_count_api(from_date, to_date)` | `/1/market/count` | Aggregate market counts |

All parameters are keyword-only, except the required `from_date` / `to_date` of the version 1 count methods. Most accept either a single string or a `list[str]`; lists are comma-joined for the API. The real-time WebSocket endpoints are covered by `NewsDataApiWebSocket` (see below).

See the [NewsData.io documentation](https://newsdata.io/documentation) — or the [OpenAPI 3.1 spec](https://newsdata.io/openapi.json) — for the full parameter reference.

## Version 1 and version 2

Both versions serve the same news. They differ in method names, parameter names and response layout:

| Version 1 | Version 2 |
|-----------|-----------|
| `latest_api()`, `archive_api()` | `news()` |
| `crypto_api()`, `market_api()`, `sources_api()` | `crypto()`, `market()`, `sources()` |
| `count_api()`, `crypto_count_api()`, `market_count_api()` | `count_news()`, `count_crypto()`, `count_market()` |
| `qInTitle`, `qInMeta` | `q_in_title`, `q_in_meta` |
| `domainurl`, `excludedomainurl`, `excludedomain` | `source_url`, `exclude_source_url`, `exclude_source_url` |
| `domain` | `source_url`, with the source's URL (`bbc.com`) instead of its id (`bbc`) |
| `prioritydomain` | `source_priority` |
| `excludecountry`, `excludecategory`, `excludelanguage` | `exclude_country`, `exclude_category`, `exclude_language` |
| `excludefield`, `removeduplicate` | `exclude_field`, `remove_duplicate` |
| `full_content` | `content` |
| `totalResults`, `nextPage` in the response | `total_results`, `next_page` |

Version 2 articles use `url` instead of `link`, and group related fields under `media`, `source` and `ai`. The version 2 count methods take `from_date` and `to_date` as optional keyword arguments; the version 1 count methods require them.

## Three ways to consume an endpoint

```python
# 1. Single request (the default).
response = client.news(q="news")

# 2. Auto-merge — follow next_page cursors and return one combined dict.
merged = client.news(q="news", scroll=True, max_result=200)

# 3. Iterate one response per page (a generator).
for page in client.news(q="news", paginate=True, max_pages=5):
    process(page["results"])
```

`scroll` and `paginate` are mutually exclusive. `scroll=True` truncates strictly to `max_result`; `paginate=True` stops at `max_pages` or when the API returns no `next_page`. The version 1 methods support the same three modes (for example `client.latest_api(q="news", paginate=True)`), following `nextPage` instead.

## Real-time news (WebSocket)

Requires Python 3.10 or newer. The real-time service is part of API version 2. Register a query first — the returned `registration_id` identifies it from then on:

```python
from newsdataapi import NewsDataApiClient, NewsDataApiWebSocket

client = NewsDataApiClient("YOUR_API_KEY")
ws = NewsDataApiWebSocket(client)
response = ws.websocket_register(q="bitcoin", language="en")
registration_id = response["results"]["registration_id"]
```

`websocket_register` takes the same filter parameters as `news()`, under the same names (`q`, `q_in_title`, `country`, `exclude_country`, `source_url`, `content`, `exclude_field`, `timezone`, …); the date, paging and sorting parameters, `id` and `url` don't apply to a standing query. Registering an identical query twice raises `NewsdataAPIError` with `status_code=409` — the existing id is in `e.response_body["results"]["registration_id"]`. `websocket_fetch()` lists every registered query: its `results` list has one entry per query, with the `registration_id`, the filters it was registered with (`query`), the number of devices streaming it now (`active_clients`) and when a device last connected (`last_used`, in UTC). `websocket_delete(registration_id)` removes one.

Then stream. Each yielded response has `status`, `total_results` and `results` keys, and its articles have the same layout as `news()` results (`id`, `url`, `published_at`, …, with related fields grouped under `media`, `source` and `ai`); the registration's `exclude_field` and `timezone` apply to them:

```python
for response in ws.stream(registration_id):
    for article in response["results"]:
        print(article["title"], "-", article["url"])
```

Use it as a context manager to close the connection promptly when you stop early (otherwise it closes when iteration ends):

```python
with NewsDataApiWebSocket(client) as ws:
    for response in ws.stream(registration_id):
        print(response["total_results"])
        break
```

Inside asyncio applications use `stream_async()` — the same class, same behavior, awaited iteration:

```python
import asyncio

async def main():
    async with NewsDataApiWebSocket(client) as ws:
        async for response in ws.stream_async(registration_id):
            for article in response["results"]:
                print(article["title"], "-", article["url"])

asyncio.run(main())
```

Transient drops (network errors, server restarts, abnormal closes) are reconnected automatically with a capped exponential backoff. Pass `reconnect=False` to stop on the first disconnect instead. A permanent rejection — bad API key, missing WebSocket entitlement, unknown `registration_id`, device limit reached, or exhausted quota — raises `NewsdataWebSocketAuthError` and is **not** retried:

```python
from newsdataapi import NewsdataWebSocketAuthError, NewsdataWebSocketError

try:
    for response in NewsDataApiWebSocket(client).stream(registration_id):
        ...
except NewsdataWebSocketAuthError as e:
    print(f"rejected: {e}")
except NewsdataWebSocketError as e:
    print(f"stream error: {e}")
```

All connection options are keyword-only:

```python
ws = NewsDataApiWebSocket(
    client,
    base_url="wss://ws.newsdata.io/ws/event",  # override for staging / self-hosted / proxied
    reconnect=True,                   # auto-reconnect on transient drops; default True
    reconnect_delay=1.0,              # seconds before first reconnect (doubles each retry)
    reconnect_delay_max=30.0,         # cap on the reconnect delay
    open_timeout=10.0,                # handshake timeout (None disables)
    ping_interval=20.0,               # keepalive ping interval (None disables)
    ping_timeout=20.0,                # wait for ping reply before dropping (None disables)
    additional_headers={"X-Trace": "abc"},  # extra handshake headers
    proxy="http://host:port",         # proxy URL
)
```

## Error handling

```python
from newsdataapi import (
    NewsdataAPIError,
    NewsdataApiKeyLimitExceededError,
    NewsdataApiLimitExceededError,
    NewsdataAuthError,
    NewsdataNetworkError,
    NewsdataRateLimitError,
)

try:
    client.news(q="news")
except NewsdataAuthError as e:
    print(f"bad API key (HTTP {e.status_code})")
except NewsdataApiKeyLimitExceededError:
    print("this API key's own credit cap is exhausted")
except NewsdataApiLimitExceededError:
    print("account credit pool is exhausted")
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
├── NewsdataValidationError              (also a ValueError; carries .param)
├── NewsdataAPIError                     (carries .status_code, .response_body)
│   ├── NewsdataAuthError                (401 / 403)
│   ├── NewsdataRateLimitError           (429; carries .retry_after)
│   │   ├── NewsdataApiLimitExceededError      (account credit pool exhausted)
│   │   └── NewsdataApiKeyLimitExceededError   (this API key's own credit cap exhausted)
│   └── NewsdataServerError              (5xx)
├── NewsdataNetworkError                 (carries .original)
└── NewsdataWebSocketError               (real-time stream)
    └── NewsdataWebSocketAuthError  (handshake 401 / 403, or policy-violation close 1008)
```

`NewsdataApiLimitExceededError` and `NewsdataApiKeyLimitExceededError` are both subclasses of `NewsdataRateLimitError`, so existing code that only catches `NewsdataRateLimitError` keeps working unchanged — catch the specific subclasses only if you want to react differently to each. Neither is ever retried.

`NewsdataException` is always a valid catch-all.

When a request succeeds and `include_headers=True`, the response dict's `response_headers` also carries `X-API-Limit-Remaining` (account pool) and, for API keys with a credit cap, `X-APIKEY-Limit-Remaining` (that key's own remaining credits).

## Save results to CSV

```python
client.save_to_csv(response, folder_path="./out", filename="latest_news")

# Or set folder_path once on the client and reuse:
client = NewsDataApiClient(apikey, folder_path="./out")
client.save_to_csv(response, filename="latest_news")
```

`save_to_csv` returns a `pathlib.Path`. Nested fields get one column each, named with dots (`source.name`, `ai.sentiment.label`); lists are comma-joined, and lists of objects are written as JSON. Responses from the version 1 methods keep the version 1 format: dict and list cells are stringified (`key:value,key:value` for dicts, comma-joined for lists). Quoting is delegated to the standard `csv.DictWriter`, so the output round-trips correctly through any CSV reader.

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
    proxies={"https": "..."},   # passed with every request
    accept_language="en",       # Accept-Language header
    include_headers=False,      # if True, returned dicts include response_headers
    base_url="...",             # API root; override for staging / proxied environments
    session=my_session,         # inject your own requests.Session
    folder_path="./out",        # default folder for save_to_csv; default None
)
```

`base_url` (and `set_base_url()`) is the API root without a version segment; the default is `https://newsdata.io/api`, and the client adds `/1/...` or `/2/...` itself. Before 0.4.0 it included the version (`https://newsdata.io/api/1/`), so drop the trailing `/1/` if you override it.

A request that fails with a server error, a rate limit, or a network error is attempted 5 times by default, sleeping 2 s, 4 s, 8 s and 16 s between attempts (30 s in total; a single sleep never exceeds `retry_backoff_max`). A 429 response is instead retried after the server's `Retry-After` plus one second (both integer-seconds and HTTP-date forms are parsed); when `Retry-After` is longer than `retry_backoff_max`, the client does not wait and raises `NewsdataRateLimitError` with `retry_after` set. A 429 that waiting cannot fix is raised at once, without retrying: `ApiLimitExceeded` and `ApiKeyLimitExceeded` (credits used up) and `RegistrationLimitExceeded` (all the real-time registrations the plan allows are in use; delete one to free a slot). The API key is redacted in log output.

## Development

This project uses [uv](https://github.com/astral-sh/uv) for environment and lock management.

```bash
git clone https://github.com/newsdataapi/python-client
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

## Related libraries

Official Newsdata.io clients across languages and runtimes:

- **Node.js** — [newsdataapi/newsdata-nodejs-client](https://github.com/newsdataapi/newsdata-nodejs-client) ([npm](https://www.npmjs.com/package/newsdata-nodejs-client))
- **React (hooks)** — [newsdataapi/newsdata-reactjs-client](https://github.com/newsdataapi/newsdata-reactjs-client) ([npm](https://www.npmjs.com/package/newsdataapi))
- **PHP** — [newsdataapi/php-client](https://github.com/newsdataapi/php-client) ([Packagist](https://packagist.org/packages/newsdataio/newsdataapi))
- **Java** — [newsdataapi/newsdata-java-sdk](https://github.com/newsdataapi/newsdata-java-sdk) ([Maven Central](https://central.sonatype.com/artifact/io.newsdata/newsdataapi))
- **.NET** — [newsdataapi/newsdata-dotnet-sdk](https://github.com/newsdataapi/newsdata-dotnet-sdk) ([NuGet](https://www.nuget.org/packages/Newsdata.Api/))
- **Go** — [newsdataapi/newsdata-go-client](https://github.com/newsdataapi/newsdata-go-client) ([pkg.go.dev](https://pkg.go.dev/github.com/newsdataapi/newsdata-go-client))
- **Dart / Flutter** — [newsdataapi/newsdata-flutter-client](https://github.com/newsdataapi/newsdata-flutter-client) ([pub.dev](https://pub.dev/packages/newsdataapi))
- **MCP Server (AI assistants)** — [newsdataapi/newsdata.io-mcp](https://github.com/newsdataapi/newsdata.io-mcp) ([PyPI](https://pypi.org/project/newsdata-mcp/))

Also see [free news datasets](https://github.com/newsdataapi/newsdata.io-free-datasets) for ML / NLP work.

## License

MIT. See the [LICENSE](LICENSE) file.

"""Constants used by the :mod:`newsdataapi` client."""

from __future__ import annotations

# Root URL of the NewsData.io REST API. Endpoint paths carry the API version
# and are joined to it (the client adds the trailing slash ``urljoin`` needs).
BASE_URL = "https://newsdata.io/api"

# v1 endpoint paths, joined to ``BASE_URL`` to form the full request URL.
LATEST_ENDPOINT = "1/latest"
ARCHIVE_ENDPOINT = "1/archive"
SOURCES_ENDPOINT = "1/sources"
CRYPTO_ENDPOINT = "1/crypto"
MARKET_ENDPOINT = "1/market"
COUNT_ENDPOINT = "1/count"
CRYPTO_COUNT_ENDPOINT = "1/crypto/count"
MARKET_COUNT_ENDPOINT = "1/market/count"

# v2 endpoint paths.
NEWS_V2_ENDPOINT = "2/news"
MARKET_V2_ENDPOINT = "2/market"
CRYPTO_V2_ENDPOINT = "2/crypto"
SOURCES_V2_ENDPOINT = "2/sources"
COUNT_NEWS_V2_ENDPOINT = "2/count/news"
COUNT_MARKET_V2_ENDPOINT = "2/count/market"
COUNT_CRYPTO_V2_ENDPOINT = "2/count/crypto"
WEBSOCKET_REGISTER_ENDPOINT = "2/websocket/register"
WEBSOCKET_FETCH_ENDPOINT = "2/websocket/fetch"
WEBSOCKET_DELETE_ENDPOINT = "2/websocket/delete"

# HTTP defaults.
DEFAULT_REQUEST_TIMEOUT = 30          # seconds
DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_BACKOFF = 2.0           # base seconds; doubles each attempt
DEFAULT_RETRY_BACKOFF_MAX = 60.0      # cap on any single retry sleep
PAGINATION_DELAY = 1.0                # seconds slept between pages

# Real-time WebSocket defaults (newsdataapi.NewsDataApiWebSocket).
WS_BASE_URL = "wss://ws.newsdata.io/ws/event"
WS_NEWS_TYPE = "news"           # feed a registered query matches against (only news so far)
WS_POLICY_VIOLATION = 1008      # close code for a permanent connection rejection
WS_RECONNECT_DELAY = 1.0        # seconds before the first reconnect; doubles each retry
WS_RECONNECT_DELAY_MAX = 30.0   # cap on the reconnect delay

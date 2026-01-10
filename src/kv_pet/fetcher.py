"""HTTP fetcher with session reuse, rate limiting, and retries."""

import random
import time
from typing import Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    BASE_URL,
    DEFAULT_HEADERS,
    MAX_RETRIES,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF,
)
from .criteria import SearchCriteria


class RateLimitedSession:
    """HTTP session with rate limiting and retry logic."""

    def __init__(
        self,
        delay_min: float = REQUEST_DELAY_MIN,
        delay_max: float = REQUEST_DELAY_MAX,
        max_retries: int = MAX_RETRIES,
        headers: Optional[dict] = None,
    ):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.last_request_time: Optional[float] = None

        self.session = requests.Session()
        self.session.headers.update(headers or DEFAULT_HEADERS)

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _wait_for_rate_limit(self) -> None:
        """Wait if needed to respect rate limit."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            delay = random.uniform(self.delay_min, self.delay_max)
            if elapsed < delay:
                time.sleep(delay - elapsed)

    def get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """Make a rate-limited GET request."""
        self._wait_for_rate_limit()
        self.last_request_time = time.time()

        response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        return response

    def close(self) -> None:
        """Close the session."""
        self.session.close()


class KvFetcher:
    """Fetcher for kv.ee pages."""

    def __init__(self, session: Optional[RateLimitedSession] = None):
        self.session = session or RateLimitedSession()

    def fetch_search_results(self, criteria: SearchCriteria) -> requests.Response:
        """Fetch search results page for given criteria."""
        params = criteria.to_query_params()
        return self.session.get(BASE_URL, params=params)

    def fetch_listing(self, listing_id: str) -> requests.Response:
        """Fetch individual listing page."""
        url = f"{BASE_URL}/{listing_id}.html"
        return self.session.get(url)

    def fetch_url(self, url: str) -> requests.Response:
        """Fetch arbitrary URL."""
        return self.session.get(url)

    def close(self) -> None:
        """Close the fetcher session."""
        self.session.close()

    def __enter__(self) -> "KvFetcher":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def build_search_url(criteria: SearchCriteria) -> str:
    """Build full search URL from criteria (for debugging/logging)."""
    params = criteria.to_query_params()
    return f"{BASE_URL}?{urlencode(params)}"

"""HTTP fetcher with session reuse, rate limiting, and anti-bot handling."""

import random
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    BASE_URL,
    DEFAULT_HEADERS,
    HEADLESS_FALLBACK_ENABLED,
    MAX_RETRIES,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF,
)
from .criteria import SearchCriteria


@dataclass
class FetchResult:
    """Result of a fetch operation."""

    html: str
    status_code: int
    url: str
    is_blocked: bool = False
    block_reason: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.status_code == 200 and not self.is_blocked


class AntiBlockDetector:
    """Detect anti-bot blocking patterns in responses."""

    CLOUDFLARE_INDICATORS = [
        "cf-mitigated",
        "cf-ray",
        "__cf_bm",
        "challenge-platform",
        "Just a moment...",
    ]

    @classmethod
    def is_blocked(cls, response: requests.Response) -> tuple[bool, Optional[str]]:
        """Check if response indicates blocking.

        Returns (is_blocked, reason).
        """
        # Check for explicit 403
        if response.status_code == 403:
            # Check for Cloudflare challenge
            if "cf-mitigated" in response.headers.get("", ""):
                return True, "Cloudflare JS challenge"
            for header in response.headers:
                if header.lower().startswith("cf-"):
                    return True, "Cloudflare protection"
            return True, "HTTP 403 Forbidden"

        # Check response content for challenge pages
        content = response.text[:5000].lower()
        if "just a moment" in content and "cloudflare" in content:
            return True, "Cloudflare JS challenge page"
        if "enable javascript" in content:
            return True, "JavaScript required"
        if "captcha" in content:
            return True, "CAPTCHA challenge"

        return False, None


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

    def get(
        self, url: str, params: Optional[dict] = None, referer: Optional[str] = None
    ) -> requests.Response:
        """Make a rate-limited GET request."""
        self._wait_for_rate_limit()
        self.last_request_time = time.time()

        headers = {}
        if referer:
            headers["Referer"] = referer

        response = self.session.get(
            url, params=params, timeout=REQUEST_TIMEOUT, headers=headers
        )
        # Force UTF-8 encoding for Estonian characters (õ, ä, ö, ü)
        # This prevents chardet from mis-detecting the encoding
        response.encoding = "utf-8"
        return response

    def close(self) -> None:
        """Close the session."""
        self.session.close()


class HeadlessFetcher:
    """Fallback fetcher using headless browser for JS-protected sites.

    Uses playwright-stealth to avoid bot detection.
    Requires: pip install playwright playwright-stealth && playwright install chromium
    """

    def __init__(self, use_stealth: bool = True):
        self._browser = None
        self._context = None
        self._page = None
        self._use_stealth = use_stealth

    def _ensure_browser(self):
        """Lazy-initialize browser with stealth mode."""
        if self._browser is not None:
            return

        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            # Create context with realistic viewport and user agent
            self._context = self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="Europe/Tallinn",
            )

            self._page = self._context.new_page()

            # Apply stealth mode if available
            if self._use_stealth:
                try:
                    from playwright_stealth import stealth_sync
                    stealth_sync(self._page)
                except ImportError:
                    pass  # Continue without stealth if not installed

        except ImportError:
            raise RuntimeError(
                "Headless fallback requires playwright. "
                "Install with: pip install playwright playwright-stealth && playwright install chromium"
            )
        except Exception as e:
            error_msg = str(e)
            if "libgbm" in error_msg or "shared libraries" in error_msg:
                raise RuntimeError(
                    "Headless browser missing system dependencies. "
                    "On Ubuntu/Debian: sudo apt install libgbm1 libasound2 libatk-bridge2.0-0 libgtk-3-0\n"
                    "Or run: sudo playwright install-deps chromium"
                )
            raise RuntimeError(f"Failed to launch headless browser: {e}")

    def get(self, url: str, timeout: int = 60000) -> FetchResult:
        """Fetch URL using headless browser."""
        self._ensure_browser()

        try:
            # Navigate to page
            self._page.goto(url, wait_until="domcontentloaded", timeout=timeout)

            # Wait for Cloudflare challenge to complete (up to 15 seconds)
            for _ in range(5):
                self._page.wait_for_timeout(3000)
                html = self._page.content()
                # Check if we passed the challenge
                if "Just a moment" not in html:
                    break

            html = self._page.content()

            # Final check if still blocked
            if "Just a moment" in html:
                return FetchResult(
                    html=html,
                    status_code=403,
                    url=self._page.url,
                    is_blocked=True,
                    block_reason="Cloudflare detected headless browser",
                )

            return FetchResult(
                html=html,
                status_code=200,
                url=self._page.url,
                is_blocked=False,
            )
        except Exception as e:
            return FetchResult(
                html="",
                status_code=0,
                url=url,
                is_blocked=True,
                block_reason=f"Headless browser error: {e}",
            )

    def close(self):
        """Close browser."""
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._playwright.stop()
            self._browser = None


class KvFetcher:
    """Fetcher for kv.ee pages with anti-bot handling."""

    def __init__(
        self,
        session: Optional[RateLimitedSession] = None,
        use_headless_fallback: bool = HEADLESS_FALLBACK_ENABLED,
    ):
        self.session = session or RateLimitedSession()
        self.use_headless_fallback = use_headless_fallback
        self._headless: Optional[HeadlessFetcher] = None

    def fetch_search_results(self, criteria: SearchCriteria) -> FetchResult:
        """Fetch search results page for given criteria."""
        params = criteria.to_query_params()
        return self._fetch_with_fallback(BASE_URL, params, referer=BASE_URL)

    def fetch_listing(self, listing_id: str) -> FetchResult:
        """Fetch individual listing page."""
        url = f"{BASE_URL}/{listing_id}.html"
        return self._fetch_with_fallback(url, referer=BASE_URL)

    def fetch_url(self, url: str) -> FetchResult:
        """Fetch arbitrary URL."""
        return self._fetch_with_fallback(url)

    def _fetch_with_fallback(
        self,
        url: str,
        params: Optional[dict] = None,
        referer: Optional[str] = None,
    ) -> FetchResult:
        """Fetch URL, falling back to headless browser if blocked."""
        # Try regular HTTP first
        response = self.session.get(url, params=params, referer=referer)
        is_blocked, block_reason = AntiBlockDetector.is_blocked(response)

        if not is_blocked:
            return FetchResult(
                html=response.text,
                status_code=response.status_code,
                url=str(response.url),
                is_blocked=False,
            )

        # Blocked - try headless fallback if enabled
        if self.use_headless_fallback:
            try:
                if self._headless is None:
                    self._headless = HeadlessFetcher()

                full_url = response.url  # Use the actual URL after redirects
                return self._headless.get(str(full_url))
            except RuntimeError as e:
                # Playwright not installed
                return FetchResult(
                    html=response.text,
                    status_code=response.status_code,
                    url=str(response.url),
                    is_blocked=True,
                    block_reason=f"{block_reason}. Headless fallback failed: {e}",
                )

        return FetchResult(
            html=response.text,
            status_code=response.status_code,
            url=str(response.url),
            is_blocked=True,
            block_reason=block_reason,
        )

    def close(self) -> None:
        """Close the fetcher session."""
        self.session.close()
        if self._headless:
            self._headless.close()

    def __enter__(self) -> "KvFetcher":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def build_search_url(criteria: SearchCriteria) -> str:
    """Build full search URL from criteria (for debugging/logging)."""
    params = criteria.to_query_params()
    return f"{BASE_URL}?{urlencode(params)}"

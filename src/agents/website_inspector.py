from bs4 import BeautifulSoup
from typing import List, Set
from urllib.parse import urljoin, urlparse

from src.models.schemas import WebsiteInspectionResult
from src.utils.http_client import HTTPClient
from config.settings import CTA_KEYWORDS


IMPORTANT_KEYWORDS = [
    "about", "service", "contact",
    "pricing", "solution", "company"
]

EXCLUDE_KEYWORDS = [
    "blog", "career", "privacy",
    "terms", "login", "signup"
]


class WebsiteInspector:
    """
    AGENT 1: Website Inspector (SMART DRIFT)

    - Starts from given URL
    - Drifts to important internal pages
    - Same-domain only
    - Hard page limit
    - Deterministic & factual
    """

    def __init__(self, cta_keywords: List[str] = None, max_pages: int = 5):
        self.cta_keywords = cta_keywords or CTA_KEYWORDS
        self.max_pages = max_pages
        self.http_client = HTTPClient()

    def inspect(self, website_url: str) -> WebsiteInspectionResult:
        if not website_url or website_url.strip() == "":
            return WebsiteInspectionResult(website_exists=False)

        visited: Set[str] = set()
        pages_html: List[str] = []

        parsed_base = urlparse(website_url)

        def should_visit(url: str) -> bool:
            url_l = url.lower()
            return (
                parsed_base.netloc == urlparse(url).netloc
                and any(k in url_l for k in IMPORTANT_KEYWORDS)
                and not any(k in url_l for k in EXCLUDE_KEYWORDS)
            )

        def fetch(url: str):
            if url in visited or len(visited) >= self.max_pages:
                return

            success, response, error = self.http_client.get(url)
            if not success or not response:
                return

            visited.add(url)
            pages_html.append(response.text)

            soup = BeautifulSoup(response.text, "html.parser")
            for a in soup.find_all("a", href=True):
                next_url = urljoin(url, a["href"])
                if should_visit(next_url):
                    fetch(next_url)

        # 🔁 Start drift
        fetch(website_url)

        if not pages_html:
            return WebsiteInspectionResult(
                website_exists=True,
                is_reachable=False,
                error_message="Website not reachable"
            )

        # 🔍 Aggregate analysis across all visited pages
        combined_html = " ".join(pages_html)

        return WebsiteInspectionResult(
            website_exists=True,
            is_reachable=True,
            has_https=website_url.startswith("https://"),
            has_mobile_viewport=self._check_mobile_viewport(combined_html),
            has_cta=self._check_cta_keywords(combined_html),
            pages_visited=len(visited)  # ← optional but VERY useful
        )

    def _check_mobile_viewport(self, html: str) -> bool:
        try:
            soup = BeautifulSoup(html, "html.parser")
            return soup.find("meta", attrs={"name": "viewport"}) is not None
        except Exception:
            return False

    def _check_cta_keywords(self, html: str) -> bool:
        try:
            html_lower = html.lower()
            return any(keyword in html_lower for keyword in self.cta_keywords)
        except Exception:
            return False

    def close(self):
        self.http_client.close()

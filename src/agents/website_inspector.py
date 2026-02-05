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
        soup = BeautifulSoup(combined_html, "html.parser")

        return WebsiteInspectionResult(
            website_exists=True,
            is_reachable=True,
            has_https=website_url.startswith("https://"),
            has_mobile_viewport=self._check_mobile_viewport(combined_html),
            has_cta=self._check_cta_keywords(combined_html),
            pages_visited=len(visited),  # ← optional but VERY useful
            has_meta_description=self._has_meta_description(soup),
            has_h1=self._has_h1(soup),
            has_open_graph=self._has_open_graph(soup),
            has_contact_form=self._has_contact_form(soup),
            has_booking=self._has_booking(soup),
            has_chat_widget=self._has_chat_widget(soup),
            has_testimonials=self._has_testimonials(soup),
            has_social_links=self._has_social_links(soup),
            has_analytics=self._has_analytics(soup),
            has_structured_data=self._has_structured_data(soup),
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

    def _has_meta_description(self, soup: BeautifulSoup) -> bool:
        try:
            return soup.find("meta", attrs={"name": "description"}) is not None
        except Exception:
            return False

    def _has_h1(self, soup: BeautifulSoup) -> bool:
        try:
            return soup.find("h1") is not None
        except Exception:
            return False

    def _has_open_graph(self, soup: BeautifulSoup) -> bool:
        try:
            return soup.find("meta", attrs={"property": "og:title"}) is not None
        except Exception:
            return False

    def _has_contact_form(self, soup: BeautifulSoup) -> bool:
        try:
            forms = soup.find_all("form")
            for form in forms:
                classes = " ".join(form.get("class", []))
                identifier = f"{form.get('id', '')} {classes}".lower()
                if form.find("input", attrs={"type": "email"}) or "contact" in identifier:
                    return True
            return False
        except Exception:
            return False

    def _has_booking(self, soup: BeautifulSoup) -> bool:
        try:
            keywords = ["book", "booking", "appointment", "schedule", "calendly", "acuity", "setmore"]
            text = soup.get_text(" ").lower()
            if any(k in text for k in keywords):
                return True
            for a in soup.find_all("a", href=True):
                if any(k in a["href"].lower() for k in keywords):
                    return True
            return False
        except Exception:
            return False

    def _has_chat_widget(self, soup: BeautifulSoup) -> bool:
        try:
            providers = ["intercom", "tawk", "crisp", "drift", "livechat", "chatbot", "zendesk", "hubspot"]
            scripts = " ".join([s.get("src", "") for s in soup.find_all("script")])
            text = soup.get_text(" ").lower()
            return any(p in scripts.lower() or p in text for p in providers)
        except Exception:
            return False

    def _has_testimonials(self, soup: BeautifulSoup) -> bool:
        try:
            text = soup.get_text(" ").lower()
            return "testimonial" in text or "what our clients say" in text or "reviews" in text
        except Exception:
            return False

    def _has_social_links(self, soup: BeautifulSoup) -> bool:
        try:
            socials = ["facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "tiktok.com", "youtube.com"]
            for a in soup.find_all("a", href=True):
                if any(s in a["href"].lower() for s in socials):
                    return True
            return False
        except Exception:
            return False

    def _has_analytics(self, soup: BeautifulSoup) -> bool:
        try:
            scripts = " ".join([s.get("src", "") for s in soup.find_all("script")]).lower()
            text = soup.get_text(" ").lower()
            return any(k in scripts or k in text for k in ["gtag", "google-analytics", "gtm.js", "mixpanel", "plausible", "fathom"])
        except Exception:
            return False

    def _has_structured_data(self, soup: BeautifulSoup) -> bool:
        try:
            return soup.find("script", attrs={"type": "application/ld+json"}) is not None
        except Exception:
            return False

    def close(self):
        self.http_client.close()

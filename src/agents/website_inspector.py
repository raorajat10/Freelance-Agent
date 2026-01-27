from bs4 import BeautifulSoup
from typing import List
from src.models.schemas import WebsiteInspectionResult
from src.utils.http_client import HTTPClient
from config.settings import CTA_KEYWORDS


class     WebsiteInspector:
    """
    AGENT 1: Website Inspector
    
    Responsibilities:
    - Check if website exists
    - Verify HTTP reachability
    - Detect HTTPS
    - Detect mobile viewport meta tag
    - Detect CTA keywords
    
    This agent is deterministic and fact-based only.
    """
    
    def __init__(self, cta_keywords: List[str] = None):
        self.cta_keywords = cta_keywords or CTA_KEYWORDS
        self.http_client = HTTPClient()
    
    def inspect(self, website_url: str) -> WebsiteInspectionResult:
        """
        Inspect a website and return factual findings
        
        Args:
            website_url: The URL to inspect (empty string if no website)
            
        Returns:
            WebsiteInspectionResult with factual data
        """
        # Case 1: No website URL provided
        if not website_url or website_url.strip() == "":
            return WebsiteInspectionResult(website_exists=False)
        
        # Case 2: Website URL exists - check it
        success, response, error = self.http_client.get(website_url)
        
        if not success:
            return WebsiteInspectionResult(
                website_exists=True,
                is_reachable=False,
                error_message=error
            )
        
        # Website is reachable - inspect it
        has_https = website_url.startswith('https://')
        has_mobile_viewport = self._check_mobile_viewport(response.text)
        has_cta = self._check_cta_keywords(response.text)
        
        return WebsiteInspectionResult(
            website_exists=True,
            is_reachable=True,
            has_https=has_https,
            has_mobile_viewport=has_mobile_viewport,
            has_cta=has_cta
        )
    
    def _check_mobile_viewport(self, html: str) -> bool:
        """Check for mobile viewport meta tag"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
            return viewport_tag is not None
        except:
            return False
    
    def _check_cta_keywords(self, html: str) -> bool:
        """Check for presence of CTA keywords in HTML"""
        try:
            html_lower = html.lower()
            return any(keyword in html_lower for keyword in self.cta_keywords)
        except:
            return False
    
    def close(self):
        """Clean up resources"""
        self.http_client.close()
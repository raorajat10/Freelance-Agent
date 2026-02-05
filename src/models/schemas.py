from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class WebsiteStatus(str, Enum):
    NO_WEBSITE = "No Website"
    WEAK_WEBSITE = "Weak Website"
    ACCEPTABLE_WEBSITE = "Acceptable Website"


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class LeadInput(BaseModel):
    """Input schema for a business lead"""
    business_name: str
    category: str
    city: str
    state: str
    website_url: Optional[str] = ""
    email: Optional[str] = ""

    @field_validator('website_url', mode='before')
    def normalize_website_url(cls, v):
        if not v or v.strip() == "":
            return ""
        url = v.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url

    @field_validator('email', mode='before')
    def normalize_email(cls, v):
        return v.strip().lower() if v else ""


class WebsiteInspectionResult(BaseModel):
    """Output from Agent 1: Website Inspector"""
    website_exists: bool
    is_reachable: bool = False
    has_https: bool = False
    has_mobile_viewport: bool = False
    has_cta: bool = False
    pages_visited: int = 0
    has_meta_description: bool = False
    has_h1: bool = False
    has_open_graph: bool = False
    has_contact_form: bool = False
    has_booking: bool = False
    has_chat_widget: bool = False
    has_testimonials: bool = False
    has_social_links: bool = False
    has_instagram: bool = False
    has_youtube: bool = False
    has_tiktok: bool = False
    has_linkedin: bool = False
    has_analytics: bool = False
    has_structured_data: bool = False
    error_message: Optional[str] = None


class ClassificationResult(BaseModel):
    """Output from Agent 2: Website Classifier"""
    website_status: WebsiteStatus
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ScoringResult(BaseModel):
    """Output from Agent 3: Lead Scorer"""
    lead_score: int
    priority: Priority
    score_breakdown: dict = Field(default_factory=dict)


class LeadOutput(BaseModel):
    """Final output for a qualified lead"""
    business_name: str
    website_status: str
    website_issues: List[str]
    lead_score: int
    priority: str
    outreach_message: str
    recommendations: List[str] = Field(default_factory=list)

from src.models.schemas import (
    LeadInput,
    ClassificationResult,
    ScoringResult,
    WebsiteStatus,
    Priority
)
from src.utils.validators import is_free_email, is_local_service_business
from config.settings import (
    SCORE_NO_WEBSITE,
    SCORE_WEAK_WEBSITE,
    SCORE_ACCEPTABLE_WEBSITE,
    SCORE_LOCAL_SERVICE,
    SCORE_FREE_EMAIL,
    PRIORITY_HIGH_MIN,
    PRIORITY_MEDIUM_MIN,
    LOCAL_SERVICE_CATEGORIES
)


class LeadScorer:
    """
    AGENT 3: Lead Scorer
    
    Responsibilities:
    - Calculate numeric score based on exact rules
    - Assign priority level (HIGH/MEDIUM/LOW)
    - Provide score breakdown for transparency
    
    This agent uses pure logic. No machine learning or guessing.
    """
    
    def score(self, lead: LeadInput, classification: ClassificationResult) -> ScoringResult:
        """
        Score a lead based on classification and lead data
        
        Scoring Rules:
        - No Website → +10
        - Weak Website → +7
        - Acceptable Website → +0
        - Local service business → +3
        - Free email (Gmail/Yahoo) → +2
        
        Priority Rules:
        - score ≥ 10 → HIGH
        - score 6-9 → MEDIUM
        - score ≤ 5 → LOW
        
        Args:
            lead: Original lead input data
            classification: Website classification result
            
        Returns:
            ScoringResult with score, priority, and breakdown
        """
        score = 0
        breakdown = {}
        
        # Score based on website status
        if classification.website_status == WebsiteStatus.NO_WEBSITE:
            score += SCORE_NO_WEBSITE
            breakdown['website_status'] = SCORE_NO_WEBSITE
        elif classification.website_status == WebsiteStatus.WEAK_WEBSITE:
            score += SCORE_WEAK_WEBSITE
            breakdown['website_status'] = SCORE_WEAK_WEBSITE
        else:
            score += SCORE_ACCEPTABLE_WEBSITE
            breakdown['website_status'] = SCORE_ACCEPTABLE_WEBSITE
        
        # Score based on business type
        if is_local_service_business(lead.category, LOCAL_SERVICE_CATEGORIES):
            score += SCORE_LOCAL_SERVICE
            breakdown['local_service'] = SCORE_LOCAL_SERVICE
        
        # Score based on email type
        if is_free_email(lead.email):
            score += SCORE_FREE_EMAIL
            breakdown['free_email'] = SCORE_FREE_EMAIL
        
        # Determine priority
        if score >= PRIORITY_HIGH_MIN:
            priority = Priority.HIGH
        elif score >= PRIORITY_MEDIUM_MIN:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW
        
        return ScoringResult(
            lead_score=score,
            priority=priority,
            score_breakdown=breakdown
        )
from src.models.schemas import (
    WebsiteInspectionResult,
    ClassificationResult,
    WebsiteStatus
)


class WebsiteClassifier:
    """
    AGENT 2: Website Classifier
    
    Responsibilities:
    - Apply exact classification rules
    - Categorize as: No Website / Weak Website / Acceptable Website
    - List specific issues found
    
    This agent uses rule-based logic only. No subjective judgment.
    """
    
    def classify(self, inspection: WebsiteInspectionResult) -> ClassificationResult:
        """
        Classify website based on inspection results
        
        Rules:
        1. If website doesn't exist → "No Website"
        2. If website exists but missing ANY of (HTTPS, mobile viewport, CTA) → "Weak Website"
        3. Otherwise → "Acceptable Website"
        
        Args:
            inspection: Results from WebsiteInspector
            
        Returns:
            ClassificationResult with status and issues
        """
        issues = []
        
        # Rule 1: No website
        if not inspection.website_exists:
            return ClassificationResult(
                website_status=WebsiteStatus.NO_WEBSITE,
                issues=["No website found"]
            )
        
        # Website exists but not reachable
        if not inspection.is_reachable:
            return ClassificationResult(
                website_status=WebsiteStatus.WEAK_WEBSITE,
                issues=[f"Website unreachable: {inspection.error_message}"]
            )
        
        # Rule 2: Check for weakness indicators
        if not inspection.has_https:
            issues.append("Missing HTTPS")
        
        if not inspection.has_mobile_viewport:
            issues.append("Not mobile-friendly")
        
        if not inspection.has_cta:
            issues.append("No clear call-to-action")
        
        # If ANY issues found → Weak Website
        if issues:
            return ClassificationResult(
                website_status=WebsiteStatus.WEAK_WEBSITE,
                issues=issues
            )
        
        # Rule 3: All checks passed → Acceptable Website
        return ClassificationResult(
            website_status=WebsiteStatus.ACCEPTABLE_WEBSITE,
            issues=[]
        )
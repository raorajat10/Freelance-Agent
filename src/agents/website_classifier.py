from src.models.schemas import (
    WebsiteInspectionResult,
    ClassificationResult,
    WebsiteStatus
)


class WebsiteClassifier:
    """
    AGENT 2: Website Classifier (DRIFT-AWARE)

    - Deterministic
    - Rule-based
    - Uses aggregated inspection results
    """

    def classify(self, inspection: WebsiteInspectionResult) -> ClassificationResult:
        issues = []

        # Rule 1: No website
        if not inspection.website_exists:
            return ClassificationResult(
                website_status=WebsiteStatus.NO_WEBSITE,
                issues=["No website found"]
            )

        # Website exists but unreachable
        if not inspection.is_reachable:
            return ClassificationResult(
                website_status=WebsiteStatus.WEAK_WEBSITE,
                issues=[f"Website unreachable: {inspection.error_message}"]
            )

        # Drift-awareness (optional but powerful)
        pages_visited = getattr(inspection, "pages_visited", 1)

        if not inspection.has_https:
            issues.append("Missing HTTPS")

        if not inspection.has_mobile_viewport:
            issues.append("Not mobile-friendly")

        if not inspection.has_cta:
            issues.append("No clear call-to-action")

        # Extra factual signal from drift
        if pages_visited == 1:
            issues.append("Limited site structure detected")

        # If ANY issues → Weak Website
        if issues:
            return ClassificationResult(
                website_status=WebsiteStatus.WEAK_WEBSITE,
                issues=issues
            )

        return ClassificationResult(
            website_status=WebsiteStatus.ACCEPTABLE_WEBSITE,
            issues=[]
        )

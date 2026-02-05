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

    def classify(self, inspection: WebsiteInspectionResult, persona: str = "") -> ClassificationResult:
        issues = []
        recommendations = []

        # Rule 1: No website
        if not inspection.website_exists:
            return ClassificationResult(
                website_status=WebsiteStatus.NO_WEBSITE,
                issues=["No website found"],
                recommendations=[],
            )

        # Website exists but unreachable
        if not inspection.is_reachable:
            return ClassificationResult(
                website_status=WebsiteStatus.WEAK_WEBSITE,
                issues=[f"Website unreachable: {inspection.error_message}"],
                recommendations=[],
            )

        # Drift-awareness (optional but powerful)
        pages_visited = getattr(inspection, "pages_visited", 1)

        if not inspection.has_https:
            issues.append("Missing HTTPS")

        if not inspection.has_mobile_viewport:
            issues.append("Not mobile-friendly")

        if not inspection.has_cta:
            issues.append("No clear call-to-action")

        if not inspection.has_meta_description:
            issues.append("Missing meta description")

        if not inspection.has_h1:
            issues.append("Missing H1 headline")

        if not inspection.has_contact_form:
            issues.append("No contact form detected")

        # Extra factual signal from drift
        if pages_visited == 1:
            issues.append("Limited site structure detected")

        # Growth recommendations (used even when the website is acceptable)
        if not inspection.has_meta_description or not inspection.has_h1:
            recommendations.append("Improve headlines and meta descriptions for search clarity")
        if not inspection.has_cta:
            recommendations.append("Add a clear primary call-to-action")
        if not inspection.has_contact_form:
            recommendations.append("Add a short inquiry/contact form")
        if not inspection.has_chat_widget:
            recommendations.append("Add live chat or chatbot for faster inquiries")
        if not inspection.has_booking:
            recommendations.append("Add booking or appointment scheduling")
        if not inspection.has_testimonials:
            recommendations.append("Add testimonials or case studies for trust")
        if not inspection.has_social_links:
            recommendations.append("Add social proof links (LinkedIn/Instagram)")
        if not inspection.has_analytics:
            recommendations.append("Add analytics to track leads (GA4)")
        if not inspection.has_open_graph:
            recommendations.append("Add Open Graph tags for better sharing previews")
        if not inspection.has_structured_data:
            recommendations.append("Add structured data (schema.org) for SEO")

        # Persona-specific filtering
        persona_key = (persona or "").strip().lower()
        persona_filters = {
            "sales": {
                "Improve headlines and meta descriptions for search clarity",
                "Add a clear primary call-to-action",
                "Add a short inquiry/contact form",
                "Add live chat or chatbot for faster inquiries",
                "Add booking or appointment scheduling",
                "Add testimonials or case studies for trust",
                "Add social proof links (LinkedIn/Instagram)",
            },
            "editor": {
                "Improve headlines and meta descriptions for search clarity",
                "Add a clear primary call-to-action",
                "Add a short inquiry/contact form",
                "Add testimonials or case studies for trust",
                "Add Open Graph tags for better sharing previews",
                "Add social proof links (LinkedIn/Instagram)",
            },
            "seo": {
                "Improve headlines and meta descriptions for search clarity",
                "Add structured data (schema.org) for SEO",
                "Add analytics to track leads (GA4)",
                "Add Open Graph tags for better sharing previews",
            },
            "virtual assistant": {
                "Add a clear primary call-to-action",
                "Add a short inquiry/contact form",
                "Add booking or appointment scheduling",
                "Add live chat or chatbot for faster inquiries",
            },
            "video editor": {
                "Add a clear primary call-to-action",
                "Add a short inquiry/contact form",
                "Add testimonials or case studies for trust",
                "Add social proof links (LinkedIn/Instagram)",
                "Add Open Graph tags for better sharing previews",
            },
            "graphic designer": {
                "Add a clear primary call-to-action",
                "Add a short inquiry/contact form",
                "Add testimonials or case studies for trust",
                "Add social proof links (LinkedIn/Instagram)",
                "Add Open Graph tags for better sharing previews",
            },
            "web developer": {
                "Improve headlines and meta descriptions for search clarity",
                "Add a clear primary call-to-action",
                "Add a short inquiry/contact form",
                "Add structured data (schema.org) for SEO",
                "Add analytics to track leads (GA4)",
                "Add Open Graph tags for better sharing previews",
                "Add live chat or chatbot for faster inquiries",
            },
        }

        if persona_key:
            matched_key = None
            for key in persona_filters.keys():
                if key in persona_key:
                    matched_key = key
                    break
            if matched_key:
                allowed = persona_filters[matched_key]
                recommendations = [r for r in recommendations if r in allowed]

        # If ANY issues → Weak Website
        if issues:
            return ClassificationResult(
                website_status=WebsiteStatus.WEAK_WEBSITE,
                issues=issues,
                recommendations=recommendations,
            )

        return ClassificationResult(
            website_status=WebsiteStatus.ACCEPTABLE_WEBSITE,
            issues=[],
            recommendations=recommendations,
        )

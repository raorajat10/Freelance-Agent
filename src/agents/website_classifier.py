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
        if not inspection.has_instagram and not inspection.has_youtube and not inspection.has_tiktok:
            recommendations.append("Add a portfolio social channel (Instagram/YouTube/TikTok)")
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
                "Add testimonials or case studies for trust",
                "Add a clear primary call-to-action",
                "Add social proof links (LinkedIn/Instagram)",
            },
            "copywriter": {
                "Improve headlines and meta descriptions for search clarity",
                "Add testimonials or case studies for trust",
                "Add a clear primary call-to-action",
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
                "Add a portfolio social channel (Instagram/YouTube/TikTok)",
            },
            "graphic designer": {
                "Add a clear primary call-to-action",
                "Add a short inquiry/contact form",
                "Add testimonials or case studies for trust",
                "Add social proof links (LinkedIn/Instagram)",
                "Add Open Graph tags for better sharing previews",
                "Add a portfolio social channel (Instagram/YouTube/TikTok)",
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
                recommendations = self._apply_persona_wording(recommendations, matched_key)
                issues = self._filter_issues_for_persona(issues, matched_key)

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

    def _filter_issues_for_persona(self, issues, persona_key: str):
        if not issues:
            return issues
        persona_issue_filters = {
            "sales": {
                "No clear call-to-action",
                "No contact form detected",
                "Limited site structure detected",
            },
            "editor": {
                "No clear call-to-action",
                "No contact form detected",
                "Missing H1 headline",
                "Missing meta description",
            },
            "copywriter": {
                "No clear call-to-action",
                "No contact form detected",
                "Missing H1 headline",
                "Missing meta description",
            },
            "seo": {
                "Missing HTTPS",
                "Not mobile-friendly",
                "Missing meta description",
                "Missing H1 headline",
                "Limited site structure detected",
            },
            "virtual assistant": {
                "No clear call-to-action",
                "No contact form detected",
            },
            "video editor": {
                "No clear call-to-action",
                "No contact form detected",
            },
            "graphic designer": {
                "No clear call-to-action",
                "No contact form detected",
            },
            "web developer": {
                "Missing HTTPS",
                "Not mobile-friendly",
                "No clear call-to-action",
                "Missing meta description",
                "Missing H1 headline",
                "No contact form detected",
                "Limited site structure detected",
            },
        }
        allowed = persona_issue_filters.get(persona_key)
        if not allowed:
            return issues
        return [i for i in issues if i in allowed]

    def _apply_persona_wording(self, recommendations, persona_key: str):
        if not recommendations:
            return recommendations
        wording = {
            "sales": {
                "Improve headlines and meta descriptions for search clarity": "Tighten the headline so the offer is clear in seconds",
                "Add a clear primary call-to-action": "Add one clear CTA (e.g., “Request a quote”) above the fold",
                "Add a short inquiry/contact form": "Add a short inquiry form to capture leads fast",
                "Add live chat or chatbot for faster inquiries": "Add live chat to capture inbound interest instantly",
                "Add booking or appointment scheduling": "Add a booking link so prospects can schedule demos",
                "Add testimonials or case studies for trust": "Add 2–3 client wins to build trust fast",
                "Add social proof links (LinkedIn/Instagram)": "Add social proof links to build credibility",
            },
            "editor": {
                "Improve headlines and meta descriptions for search clarity": "Improve the page headline and meta copy for clarity",
                "Add a clear primary call-to-action": "Add a clear CTA line in the copy",
                "Add a short inquiry/contact form": "Add a short contact form to capture briefs",
                "Add testimonials or case studies for trust": "Add client quotes or mini case studies",
                "Add Open Graph tags for better sharing previews": "Improve social share previews (Open Graph)",
                "Add social proof links (LinkedIn/Instagram)": "Add social proof links near the CTA",
            },
            "copywriter": {
                "Improve headlines and meta descriptions for search clarity": "Improve the page headline and meta copy for clarity",
                "Add a clear primary call-to-action": "Add a clear CTA line in the copy",
                "Add a short inquiry/contact form": "Add a short contact form to capture briefs",
                "Add testimonials or case studies for trust": "Add client quotes or mini case studies",
                "Add Open Graph tags for better sharing previews": "Improve social share previews (Open Graph)",
                "Add social proof links (LinkedIn/Instagram)": "Add social proof links near the CTA",
            },
            "seo": {
                "Improve headlines and meta descriptions for search clarity": "Fix H1/meta description to match search intent",
                "Add structured data (schema.org) for SEO": "Add schema markup for SEO",
                "Add analytics to track leads (GA4)": "Add GA4 to track conversions",
                "Add Open Graph tags for better sharing previews": "Add Open Graph tags for better sharing previews",
            },
            "virtual assistant": {
                "Add a clear primary call-to-action": "Add a clear CTA so visitors know the next step",
                "Add a short inquiry/contact form": "Add a short inquiry form to capture requests",
                "Add booking or appointment scheduling": "Add a booking link for quick scheduling",
                "Add live chat or chatbot for faster inquiries": "Add live chat to handle questions quickly",
            },
            "video editor": {
                "Add a clear primary call-to-action": "Add a clear CTA under the portfolio section",
                "Add a short inquiry/contact form": "Add a short form to collect project details",
                "Add testimonials or case studies for trust": "Add before/after or client testimonial snippets",
                "Add social proof links (LinkedIn/Instagram)": "Add social proof links near your work",
                "Add Open Graph tags for better sharing previews": "Improve social share previews (Open Graph)",
            },
            "graphic designer": {
                "Add a clear primary call-to-action": "Add a clear CTA under the portfolio section",
                "Add a short inquiry/contact form": "Add a short form to collect project details",
                "Add testimonials or case studies for trust": "Add client testimonials or mini case studies",
                "Add social proof links (LinkedIn/Instagram)": "Add social proof links near your work",
                "Add Open Graph tags for better sharing previews": "Improve social share previews (Open Graph)",
            },
            "web developer": {
                "Improve headlines and meta descriptions for search clarity": "Improve H1/meta to clarify value fast",
                "Add a clear primary call-to-action": "Add a clear primary CTA button",
                "Add a short inquiry/contact form": "Add a short inquiry/contact form",
                "Add structured data (schema.org) for SEO": "Add schema markup for SEO",
                "Add analytics to track leads (GA4)": "Add GA4 to track conversions",
                "Add Open Graph tags for better sharing previews": "Add Open Graph tags for better sharing previews",
                "Add live chat or chatbot for faster inquiries": "Add live chat for faster inquiries",
            },
        }
        mapper = wording.get(persona_key, {})
        return [mapper.get(r, r) for r in recommendations]

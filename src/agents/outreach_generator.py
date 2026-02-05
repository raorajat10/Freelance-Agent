from openai import OpenAI
from typing import Optional, Dict, Any

from src.models.schemas import LeadInput, ClassificationResult, ScoringResult
from config.settings import OPENAI_API_KEY, LLM_MODEL, LLM_BASE_URL
from config.prompts import OUTREACH_SYSTEM_PROMPT, OUTREACH_USER_PROMPT_TEMPLATE

OUTREACH_RELEVANT_ISSUES = {
    "Missing HTTPS",
    "Not mobile-friendly",
    "No clear call-to-action",
    "No website found",
    "Missing meta description",
    "Missing H1 headline",
    "No contact form detected",
    "Limited site structure detected"
}


class OutreachGenerator:
    """
    AGENT 4: Outreach Generator
    
    Responsibilities:
    - Generate personalized outreach message using LLM
    - Maximum 3 sentences
    - Use only verified facts from previous agents
    - Include city, business type, and price anchor ($199)
    - Professional, helpful tone
    
    This agent uses LLM but with strict constraints.
    """
    
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or LLM_MODEL
        self.base_url = base_url or LLM_BASE_URL
        
        if not self.api_key:
            raise ValueError("API key required for OutreachGenerator")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def generate(
        self,
        lead: LeadInput,
        classification: ClassificationResult,
        scoring: Optional[ScoringResult] = None,
        offer: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate outreach message
        
        Args:
            lead: Original lead data
            classification: Website classification with issues
            scoring: Lead scoring result (optional)
            offer: Optional offer/persona settings to customize messaging
            
        Returns:
            Outreach message string (max 3 sentences)
        """
        offer = offer or {}
        use_default_prompts = not offer

        persona = (offer.get("persona") or "").strip()
        service_label = (offer.get("service_label") or "").strip()
        price_anchor = (offer.get("price_anchor") or "$199").strip()

        system_prompt = (
            OUTREACH_SYSTEM_PROMPT
            if use_default_prompts
            else self._build_system_prompt(service_label=service_label, price_anchor=price_anchor)
        )

        # Format issues for the prompt
        filtered_issues = [
            issue for issue in classification.issues
            if issue in OUTREACH_RELEVANT_ISSUES
        ]

        issues_text = (", ".join(filtered_issues) if filtered_issues else "No major issues detected")
        recommendations_text = (
            ", ".join(classification.recommendations)
            if getattr(classification, "recommendations", None)
            else "None"
        )

        lead_priority = scoring.priority.value if scoring else "UNKNOWN"
        
        # Build the user prompt with ONLY verified facts
        if use_default_prompts:
            user_prompt = OUTREACH_USER_PROMPT_TEMPLATE.format(
                business_name=lead.business_name,
                category=lead.category,
                city=lead.city,
                state=lead.state,
                website_status=classification.website_status.value,
                issues=issues_text,
                recommendations=recommendations_text,
                lead_priority=lead_priority,
            )
        else:
            user_prompt = self._build_user_prompt(
                persona=persona,
                service_label=service_label,
                price_anchor=price_anchor,
                business_name=lead.business_name,
                category=lead.category,
                city=lead.city,
                state=lead.state,
                website_status=classification.website_status.value,
                issues=issues_text,
                recommendations=recommendations_text,
                lead_priority=lead_priority,
            )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=200
            )
            
            message = response.choices[0].message.content.strip()
            
            # Safety check: ensure message isn't too long
            sentences = message.split('.')
            if len(sentences) > 3:
                message = '.'.join(sentences[:3]) + '.'
            
            return message
            
        except Exception as e:
            # Fallback if LLM fails
            return self._generate_fallback(
                lead=lead,
                classification=classification,
                offer=offer,
            )
    
    def _build_system_prompt(self, service_label: str, price_anchor: str) -> str:
        safe_service_label = service_label or "freelance services"
        safe_price_anchor = price_anchor or "$199"

        return f"""You are a professional business development writer creating brief, factual outreach messages for {safe_service_label} services.

Rules:
1. Maximum 3 sentences
2. Use ONLY the facts provided
3. Do NOT make assumptions or add details not given
4. Always mention the city and business type
5. Always mention the starting price of {safe_price_anchor}
6. Professional, helpful tone
7. No marketing fluff or exaggeration

Format:
- First sentence: Acknowledge their business and location
- Second sentence: State one specific issue or improvement (if website is acceptable, use a recommendation)
- Third sentence: Brief value proposition with price anchor"""

    def _build_user_prompt(
        self,
        persona: str,
        service_label: str,
        price_anchor: str,
        business_name: str,
        category: str,
        city: str,
        state: str,
        website_status: str,
        issues: str,
        recommendations: str,
        lead_priority: str,
    ) -> str:
        return f"""Generate a brief outreach message for this business:

Freelancer role: {persona or "Freelancer"}
Service: {service_label or "Services"}
Starting price: {price_anchor or "$199"}

Business Name: {business_name}
Category: {category}
City: {city}
State: {state}
Website Status: {website_status}
Specific Issues: {issues}
Recommendations: {recommendations}
Lead priority: {lead_priority}

Generate the outreach message now."""

    def _generate_fallback(self, lead: LeadInput, classification: ClassificationResult, offer: Dict[str, Any]) -> str:
        """Deterministic fallback if LLM fails"""
        offer_line = (offer.get("offer_line") or "").strip()
        price_anchor = (offer.get("price_anchor") or "$199").strip()

        city = (lead.city or "your area").strip()
        category = (lead.category or "your business type").strip()

        if classification.website_status.value == "No Website":
            offer_line = offer_line or "Professional websites"
            return (
                f"I noticed {lead.business_name} in {city} doesn't have a website. "
                f"{offer_line} for {category} businesses start at {price_anchor}. "
                f"Would you be interested in discussing options?"
            )
        else:
            offer_line = offer_line or "Professional website upgrades"
            recommendation = ""
            if getattr(classification, "recommendations", None):
                recommendation = classification.recommendations[0]
            return (
                f"I noticed {lead.business_name}'s website in {city} could be improved. "
                f"{(recommendation + '. ') if recommendation else ''}"
                f"{offer_line} for {category} businesses start at {price_anchor}. "
                f"Would you like to discuss how I can help?"
            )

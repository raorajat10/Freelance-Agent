from openai import OpenAI
from src.models.schemas import LeadInput, ClassificationResult
from config.settings import OPENAI_API_KEY, LLM_MODEL, LLM_BASE_URL
from config.prompts import OUTREACH_SYSTEM_PROMPT, OUTREACH_USER_PROMPT_TEMPLATE


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
    
    def generate(self, lead: LeadInput, classification: ClassificationResult) -> str:
        """
        Generate outreach message
        
        Args:
            lead: Original lead data
            classification: Website classification with issues
            
        Returns:
            Outreach message string (max 3 sentences)
        """
        # Format issues for the prompt
        issues_text = ", ".join(classification.issues) if classification.issues else "No specific issues"
        
        # Build the user prompt with ONLY verified facts
        user_prompt = OUTREACH_USER_PROMPT_TEMPLATE.format(
            business_name=lead.business_name,
            category=lead.category,
            city=lead.city,
            state=lead.state,
            website_status=classification.website_status.value,
            issues=issues_text
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": OUTREACH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
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
            return self._generate_fallback(lead, classification)
    
    def _generate_fallback(self, lead: LeadInput, classification: ClassificationResult) -> str:
        """Deterministic fallback if LLM fails"""
        if classification.website_status.value == "No Website":
            return f"I noticed {lead.business_name} in {lead.city} doesn't have a website. Professional websites for {lead.category} businesses start at $199. Would you be interested in discussing how a website could help your business?"
        else:
            return f"I noticed {lead.business_name}'s website in {lead.city} could be improved. Professional website upgrades for {lead.category} businesses start at $199. Would you like to discuss how we can help?"
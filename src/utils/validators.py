import re
from typing import List
from src.models.schemas import LeadInput


def validate_lead_data(data: dict) -> LeadInput:
    """Validate and parse lead input data"""
    return LeadInput(**data)


def is_free_email(email: str) -> bool:
    """Check if email is from a free provider"""
    if not email:
        return False
    
    free_domains = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'icloud.com', 'mail.com', 'protonmail.com'
    ]
    
    domain = email.split('@')[-1].lower() if '@' in email else ''
    return domain in free_domains


def is_local_service_business(category: str, local_categories: List[str]) -> bool:
    """Check if business category is a local service"""
    category_lower = category.lower()
    return any(cat in category_lower for cat in local_categories)
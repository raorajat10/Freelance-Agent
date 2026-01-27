import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

# Google Sheets
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

# HTTP Configuration
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (compatible; LeadQualifier/1.0)")

# Business Logic
CTA_KEYWORDS = [k.strip().lower() for k in os.getenv("CTA_KEYWORDS", "call,contact,quote,estimate,free,book,schedule,consult").split(",")]
LOCAL_SERVICE_CATEGORIES = [c.strip().lower() for c in os.getenv("LOCAL_SERVICE_CATEGORIES", "plumber,electrician,hvac,landscaping,roofing,cleaning,painter,contractor").split(",")]

# Scoring Rules
SCORE_NO_WEBSITE = 10
SCORE_WEAK_WEBSITE = 7
SCORE_ACCEPTABLE_WEBSITE = 0
SCORE_LOCAL_SERVICE = 3
SCORE_FREE_EMAIL = 2

# Priority Thresholds
PRIORITY_HIGH_MIN = 10
PRIORITY_MEDIUM_MIN = 6
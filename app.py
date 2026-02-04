import streamlit as st
import pandas as pd
import json
from io import BytesIO
import os
from datetime import datetime
import sys
from pathlib import Path

# Add the project root to Python path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="Lead Qualifier Pro - AI Lead Qualification",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

COMIC_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@400;700&display=swap');

:root {
    --comic-bg: #fff7d6;
    --comic-panel: #ffffff;
    --comic-ink: #141414;
    --comic-muted: rgba(20, 20, 20, 0.7);
    --comic-primary: #ff3d00;
    --comic-secondary: #2563eb;
    --comic-accent: #fbbf24;
    --comic-success: #16a34a;
    --comic-danger: #dc2626;
    --comic-radius: 18px;
    --comic-shadow: 7px 7px 0 rgba(0,0,0,0.92);
    --comic-shadow-soft: 5px 5px 0 rgba(0,0,0,0.55);
    --comic-font-title: "Bangers", ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    --comic-font-body: "Comic Neue", ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

/* Keep the header visible so the sidebar toggle works (especially on mobile). */
header[data-testid="stHeader"] { background: transparent; border-bottom: none; }
#MainMenu { visibility: hidden; }
footer {visibility: hidden;}
.block-container { padding-top: 1.25rem; padding-bottom: 2.5rem; }

html, body, [class*="css"] { font-family: var(--comic-font-body); }
.stApp {
    background: var(--comic-bg);
    background-image:
        radial-gradient(circle at 1px 1px, rgba(0,0,0,0.08) 1px, transparent 0);
    background-size: 16px 16px;
}

h1, h2, h3, h4, h5 {
    font-family: var(--comic-font-title) !important;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: var(--comic-ink);
}

p, li, span, label, div { color: var(--comic-ink); }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff 0%, #fff7f0 100%);
    border-right: 3px solid var(--comic-ink);
}
section[data-testid="stSidebar"] * { font-family: var(--comic-font-body); }

/* Inputs */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] div[role="combobox"] {
    border: 3px solid var(--comic-ink) !important;
    border-radius: 14px !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.55) !important;
    background: #fff !important;
    color: var(--comic-ink) !important;
}

/* Selectbox text + dropdown options */
div[data-testid="stSelectbox"] span,
div[data-testid="stSelectbox"] div[role="combobox"] * {
    color: #111 !important;
}
div[data-testid="stSelectbox"] input {
    color: #111 !important;
}
div[data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] {
    color: #111 !important;
}
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[role="listbox"] {
    background: #fff !important;
    border: 3px solid var(--comic-ink) !important;
    box-shadow: var(--comic-shadow-soft) !important;
    color: #111 !important;
}
ul[role="listbox"] * {
    color: #111 !important;
}
div[role="option"] {
    background: #fff !important;
    color: #111 !important;
}
div[role="option"]:hover,
div[role="option"][aria-selected="true"] {
    background: #fef3c7 !important;
    color: white !important;
}

/* Expander chevron text issue */
/* CLEAN expander header */
div[data-testid="stExpander"] summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Hide Streamlit default arrow completely */
div[data-testid="stExpander"] summary svg,
div[data-testid="stExpander"] summary [data-testid="stIcon"] {
    display: none !important;
}

/* Add our own arrow */
div[data-testid="stExpander"] summary::after {
    content: "▾";
    font-size: 18px;
    font-weight: 900;
    color: var(--comic-ink);
    margin-left: auto;
}


/* Buttons */
div.stButton > button {
    border: 3px solid var(--comic-ink) !important;
    border-radius: 999px !important;
    box-shadow: 4px 4px 0 rgba(0,0,0,0.85) !important;
    font-weight: 800 !important;
    letter-spacing: 0.3px !important;
    transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
}
div.stButton > button:hover {
    transform: translate(-1px, -1px);
    box-shadow: 6px 6px 0 rgba(0,0,0,0.92) !important;
    filter: brightness(1.02);
}
div.stButton > button:active {
    transform: translate(1px, 1px);
    box-shadow: 3px 3px 0 rgba(0,0,0,0.85) !important;
}

/* Tabs */
div[data-testid="stTabs"] button {
    border: 3px solid var(--comic-ink) !important;
    border-radius: 999px !important;
    margin-right: 8px !important;
    box-shadow: 4px 4px 0 rgba(0,0,0,0.45) !important;
    background: #fff !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    background: var(--comic-accent) !important;
    box-shadow: 6px 6px 0 rgba(0,0,0,0.75) !important;
}

/* Expanders */
div[data-testid="stExpander"] details {
    border: 3px solid var(--comic-ink) !important;
    border-radius: var(--comic-radius) !important;
    box-shadow: var(--comic-shadow-soft) !important;
    background: #fff !important;
}

/* Dataframes */
div[data-testid="stDataFrame"] {
    border: 3px solid var(--comic-ink);
    border-radius: var(--comic-radius);
    box-shadow: var(--comic-shadow-soft);
    overflow: hidden;
}

/* Alerts (st.info/success/warning/error) */
div[data-testid="stAlert"] {
    border: 3px solid var(--comic-ink) !important;
    border-radius: var(--comic-radius) !important;
    box-shadow: var(--comic-shadow-soft) !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    border: 3px solid var(--comic-ink);
    border-radius: var(--comic-radius);
    box-shadow: 4px 4px 0 rgba(0,0,0,0.45);
    background: #fff;
    padding: 0.85rem 0.85rem;
}

/* Code blocks */
pre {
    border: 3px solid var(--comic-ink) !important;
    border-radius: var(--comic-radius) !important;
    box-shadow: var(--comic-shadow-soft) !important;
    background: #0f172a !important;
    color: #f8fafc !important;
}
pre code { color: #f8fafc !important; }

/* Custom building blocks */
.comic-hero {
    background: linear-gradient(135deg, #fff 0%, #fff3bf 100%);
    border: 4px solid var(--comic-ink);
    border-radius: calc(var(--comic-radius) + 6px);
    box-shadow: var(--comic-shadow);
    padding: 1.5rem 1.6rem;
    position: relative;
    overflow: hidden;
}
.comic-hero:before {
    content: "";
    position: absolute;
    inset: -40px;
    background:
        radial-gradient(circle at 8px 8px, rgba(0,0,0,0.09) 2px, transparent 0);
    background-size: 22px 22px;
    transform: rotate(-6deg);
    opacity: 0.55;
    pointer-events: none;
}
.comic-hero > * { position: relative; }
.comic-kicker {
    display: inline-block;
    padding: 6px 12px;
    background: var(--comic-primary);
    color: #fff !important;
    border: 3px solid var(--comic-ink);
    border-radius: 999px;
    box-shadow: 4px 4px 0 rgba(0,0,0,0.85);
    font-weight: 800;
    letter-spacing: 0.6px;
}
.comic-subtitle {
    font-size: 1.1rem;
    color: var(--comic-muted);
    margin-top: 0.4rem;
}
.comic-panel {
    background: var(--comic-panel);
    border: 3px solid var(--comic-ink);
    border-radius: var(--comic-radius);
    box-shadow: var(--comic-shadow-soft);
    padding: 1.15rem 1.15rem;
}
.comic-badge {
    display: inline-block;
    padding: 6px 10px;
    border: 2px solid var(--comic-ink);
    border-radius: 999px;
    background: #fff;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.35);
    font-weight: 700;
    margin-right: 8px;
    margin-bottom: 8px;
}
.comic-badge--alt { background: #e0f2fe; }
.comic-badge--good { background: #dcfce7; }
.comic-badge--warn { background: #fef9c3; }
.comic-badge--bad { background: #fee2e2; }
.comic-micro {
    font-size: 0.92rem;
    color: var(--comic-muted);
}
.comic-speech {
    background: #fff;
    border: 3px solid var(--comic-ink);
    border-radius: 16px;
    box-shadow: var(--comic-shadow-soft);
    padding: 0.9rem 1rem;
    position: relative;
}
.comic-speech:after {
    content: "";
    position: absolute;
    left: 22px;
    bottom: -12px;
    width: 18px;
    height: 18px;
    background: #fff;
    border-right: 3px solid var(--comic-ink);
    border-bottom: 3px solid var(--comic-ink);
    transform: rotate(45deg);
}
/* FORCE readable text in inputs + dropdowns */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] input,
div[data-testid="stSelectbox"] span,
div[data-testid="stSelectbox"] div[role="combobox"],
div[data-testid="stSelectbox"] div[role="combobox"] * {
    color: #111 !important;
}

/* Dropdown menu (BaseWeb) */
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[role="listbox"],
li[role="option"] {
    background: #fff !important;
    color: #111 !important;
}

/* Selected + hover state */
li[role="option"][aria-selected="true"],
li[role="option"]:hover {
    background: #fef3c7 !important;
    color: #111 !important;
}
div[data-testid="stExpander"] summary {
    font-weight: 700;
    letter-spacing: 0.3px;
}

</style>
"""

st.markdown(COMIC_THEME_CSS, unsafe_allow_html=True)

from src.agents.website_inspector import WebsiteInspector
from src.agents.website_classifier import WebsiteClassifier
from src.agents.lead_scorer import LeadScorer
from src.agents.outreach_generator import OutreachGenerator
from src.models.schemas import LeadInput, LeadOutput

RESULTS_DIR = "data/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# API Configuration
_openai_secret = st.secrets.get("OPENAI_API_KEY", "")
if not _openai_secret:
    try:
        _openai_secret = st.secrets.get("auth", {}).get("OPENAI_API_KEY", "")
    except Exception:
        _openai_secret = ""
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") or _openai_secret

# Payment Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
STRIPE_KEY = os.getenv("STRIPE_KEY", "")

USER_DB_FILE = "users.json"

DEFAULT_PERSONA = "Web Developer"
DEFAULT_CURRENCY_SYMBOL = "$"
PERSONA_PRESETS = {
    "Web Developer": {
        "service_label": "web design & web development",
        "offer_line": "Professional websites",
        "starting_price": 199,
    },
    "Sales / SDR Freelancer": {
        "service_label": "sales outreach",
        "offer_line": "Outbound outreach packages",
        "starting_price": 199,
    },
    "Copywriter / Editor": {
        "service_label": "copywriting and editing",
        "offer_line": "Content writing and editing",
        "starting_price": 199,
    },
    "Video Editor": {
        "service_label": "video editing",
        "offer_line": "Video editing packages",
        "starting_price": 199,
    },
    "Graphic Designer": {
        "service_label": "graphic design",
        "offer_line": "Design packages",
        "starting_price": 199,
    },
    "SEO Consultant": {
        "service_label": "SEO optimization",
        "offer_line": "SEO audits",
        "starting_price": 199,
    },
    "Virtual Assistant": {
        "service_label": "virtual assistant support",
        "offer_line": "VA support packages",
        "starting_price": 199,
    },
    "Custom": {
        "service_label": "",
        "offer_line": "",
        "starting_price": 199,
    },
}


def _format_price_anchor(currency_symbol: str, starting_price) -> str:
    symbol = (currency_symbol or DEFAULT_CURRENCY_SYMBOL).strip() or DEFAULT_CURRENCY_SYMBOL
    try:
        price_int = int(starting_price)
        return f"{symbol}{price_int}"
    except Exception:
        return f"{symbol}{starting_price}"


def get_offer_config() -> dict:
    persona = st.session_state.get("persona", DEFAULT_PERSONA) or DEFAULT_PERSONA
    service_label = st.session_state.get("offer_service_label", "") or ""
    offer_line = st.session_state.get("offer_offer_line", "") or ""
    currency_symbol = st.session_state.get("offer_currency_symbol", DEFAULT_CURRENCY_SYMBOL) or DEFAULT_CURRENCY_SYMBOL
    starting_price = st.session_state.get("offer_starting_price", PERSONA_PRESETS[DEFAULT_PERSONA]["starting_price"])

    return {
        "persona": persona,
        "service_label": service_label,
        "offer_line": offer_line,
        "starting_price": starting_price,
        "currency_symbol": currency_symbol,
        "price_anchor": _format_price_anchor(currency_symbol, starting_price),
    }


class LeadQualificationPipeline:
    def __init__(self, OPENAI_API_KEY: str, offer: dict = None):
        self.inspector = WebsiteInspector()
        self.classifier = WebsiteClassifier()
        self.scorer = LeadScorer()
        self.outreach_gen = OutreachGenerator(api_key=OPENAI_API_KEY)
        self.offer = offer or {}
    
    def process_lead(self, lead: LeadInput) -> LeadOutput:
        inspection = self.inspector.inspect(lead.website_url)
        classification = self.classifier.classify(inspection)
        scoring = self.scorer.score(lead, classification)
        
        if scoring.priority.value in ['HIGH', 'MEDIUM']:
            outreach = self.outreach_gen.generate(lead, classification, scoring, offer=self.offer)
        else:
            outreach = "Low priority - no outreach generated"
        
        return LeadOutput(
            business_name=lead.business_name,
            website_status=classification.website_status.value,
            website_issues=classification.issues,
            lead_score=scoring.lead_score,
            priority=scoring.priority.value,
            outreach_message=outreach
        )
    
    def cleanup(self):
        self.inspector.close()


def is_user_logged_in() -> bool:
    """Check if user is logged in - compatible with both local and Streamlit Cloud"""
    try:
        # Try to access is_logged_in attribute
        return st.user.is_logged_in
    except (AttributeError, KeyError):
        # Authentication not configured - use fallback
        return st.session_state.get("logged_in", False)


def get_user_email() -> str:
    """Get user email - compatible with both local and Streamlit Cloud"""
    try:
        return st.user.email
    except (AttributeError, KeyError):
        return st.session_state.get("user_email", "demo@example.com")


def get_user_name() -> str:
    """Get user name - compatible with both local and Streamlit Cloud"""
    try:
        return st.user.name
    except (AttributeError, KeyError):
        return st.session_state.get("user_name", "Demo User")


def get_results_file(user_email: str) -> str:
    """Generate safe file path for user results"""
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    return os.path.join(RESULTS_DIR, f"{safe_email}.json")


def save_results(user_email: str, results: list):
    """Save results to user-specific file"""
    path = get_results_file(user_email)
    with open(path, "w") as f:
        json.dump([r.model_dump() for r in results], f, indent=2)


def load_results(user_email: str):
    """Load results from user-specific file"""
    path = get_results_file(user_email)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def load_users():
    """Load users from database"""
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    """Save users to database"""
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f, indent=2)


def get_or_create_user(email: str, name: str = None):
    """Get existing user or create new one"""
    users = load_users()
    default_preset = PERSONA_PRESETS[DEFAULT_PERSONA]
    
    if email not in users:
        users[email] = {
            'email': email,
            'name': name or email.split('@')[0],
            'credits': 10,  # Free trial credits
            'total_processed': 0,
            'created_at': datetime.now().isoformat(),
            'subscription': 'free',
            # Persona & offer (used to tailor outreach)
            "persona": DEFAULT_PERSONA,
            "service_label": default_preset["service_label"],
            "offer_line": default_preset["offer_line"],
            "starting_price": default_preset["starting_price"],
            "currency_symbol": DEFAULT_CURRENCY_SYMBOL,
        }
        save_users(users)
    else:
        # Backfill new keys for existing users without changing auth/credits behavior
        changed = False
        user = users[email]
        if "persona" not in user:
            user["persona"] = DEFAULT_PERSONA
            changed = True
        if "service_label" not in user:
            user["service_label"] = default_preset["service_label"]
            changed = True
        if "offer_line" not in user:
            user["offer_line"] = default_preset["offer_line"]
            changed = True
        if "starting_price" not in user:
            user["starting_price"] = default_preset["starting_price"]
            changed = True
        if "currency_symbol" not in user:
            user["currency_symbol"] = DEFAULT_CURRENCY_SYMBOL
            changed = True
        if changed:
            save_users(users)
    
    return users[email]


def init_session_state():
    """Initialize session state variables"""
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'credits' not in st.session_state:
        st.session_state.credits = 0
    if "persona" not in st.session_state:
        st.session_state.persona = DEFAULT_PERSONA
    if "offer_service_label" not in st.session_state:
        st.session_state.offer_service_label = PERSONA_PRESETS[DEFAULT_PERSONA]["service_label"]
    if "offer_offer_line" not in st.session_state:
        st.session_state.offer_offer_line = PERSONA_PRESETS[DEFAULT_PERSONA]["offer_line"]
    if "offer_starting_price" not in st.session_state:
        st.session_state.offer_starting_price = PERSONA_PRESETS[DEFAULT_PERSONA]["starting_price"]
    if "offer_currency_symbol" not in st.session_state:
        st.session_state.offer_currency_symbol = DEFAULT_CURRENCY_SYMBOL
    if "offer_loaded_for" not in st.session_state:
        st.session_state.offer_loaded_for = None
    if "persona_last" not in st.session_state:
        st.session_state.persona_last = None


def calculate_priority_metrics(results):
    """Calculate priority-based metrics"""
    if not results:
        return 0, 0, 0, 0.0

    high_count = sum(1 for r in results if r.priority == "HIGH")
    medium_count = sum(1 for r in results if r.priority == "MEDIUM")
    low_count = sum(1 for r in results if r.priority == "LOW")
    avg_score = sum(r.lead_score for r in results) / len(results)

    return high_count, medium_count, low_count, avg_score


def convert_df_to_excel(df):
    """Convert DataFrame to Excel bytes"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Qualified Leads')
    return output.getvalue()


def login_page():
    st.markdown(
        """
        <div class="comic-hero">
            <span class="comic-kicker">Lead Qualification SaaS</span>
            <h1 style="margin-top: 0.75rem; margin-bottom: 0.25rem;">Lead Qualifier Pro</h1>
            <p class="comic-subtitle">
                Qualify leads, generate outreach, and focus on the work worth your time — with a comic-book vibe.
            </p>
            <div style="margin-top: 0.8rem;">
                <span class="comic-badge comic-badge--alt">Web Developers</span>
                <span class="comic-badge comic-badge--alt">Sales Freelancers</span>
                <span class="comic-badge comic-badge--alt">Editors</span>
                <span class="comic-badge comic-badge--alt">Designers</span>
                <span class="comic-badge comic-badge--alt">Agencies</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.35, 0.85], gap="large")

    with col1:
        st.markdown(
            """
            <div class="comic-panel">
                <h3 style="margin-top: 0;">What you get</h3>
                <ul style="margin-bottom: 0.5rem;">
                    <li><b>Lead scoring</b> that highlights who to contact first</li>
                    <li><b>Website signals</b> (reachability, mobile, HTTPS, CTA)</li>
                    <li><b>AI outreach drafts</b> that stay short and factual</li>
                    <li><b>CSV upload + exports</b> (Excel / CSV / JSON)</li>
                </ul>
                <div class="comic-speech" style="margin-top: 0.9rem;">
                    Turn a messy list into a clear hit‑list in minutes.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="comic-panel">
                <h3 style="margin-top: 0;">Built for modern freelancers</h3>
                <div style="margin-bottom: 0.3rem;">
                    <span class="comic-badge comic-badge--good">Web Design / Dev</span>
                    <span class="comic-badge comic-badge--good">Copywriter / Editor</span>
                    <span class="comic-badge comic-badge--good">Video Editor</span>
                    <span class="comic-badge comic-badge--good">Sales / SDR</span>
                    <span class="comic-badge comic-badge--good">SEO Consultant</span>
                    <span class="comic-badge comic-badge--good">Virtual Assistant</span>
                </div>
                <p class="comic-micro" style="margin-bottom: 0;">
                    After you sign in, pick a persona and offer so outreach matches your freelancing work.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="comic-panel">
                <h3 style="margin-top: 0;">Sign in</h3>
                <p class="comic-micro" style="margin-top: 0;">
                    Use Google to keep your workspace private and your credits tied to your account.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign in with Google", type="primary", width="stretch"):
            try:
                st.login()
            except Exception as e:
                st.error(f"Authentication error: {str(e)}")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="comic-panel">
                <h3 style="margin-top: 0;">Pricing (credits)</h3>
                <p class="comic-micro" style="margin-top: 0; margin-bottom: 0.8rem;">
                    Each qualified lead uses 1 credit.
                </p>
                <div>
                    <span class="comic-badge comic-badge--warn">Starter: 50 credits</span>
                    <span class="comic-badge comic-badge--warn">Professional: 200 credits</span>
                    <span class="comic-badge comic-badge--warn">Enterprise: 1000 credits</span>
                </div>
                <p class="comic-micro" style="margin-bottom: 0;">
                    Payments can be wired in when you’re ready.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Deployment notes (Streamlit Cloud)", expanded=False):
            st.markdown(
                """
                In Streamlit Cloud, go to **App settings → Secrets** and paste:

                ```toml
                # App keys (top-level)
                OPENAI_API_KEY = "sk-your-openai-key"
                # Optional:
                # LLM_MODEL = "gpt-4o-mini"

                [auth]
                redirect_uri = "https://your-app-name.streamlit.app/oauth2callback"
                cookie_secret = "your-secret"
                client_id = "your-google-client-id"
                client_secret = "your-google-client-secret"
                server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
                ```

                Also update your **Google OAuth** Authorized redirect URI to match:
                `https://your-app-name.streamlit.app/oauth2callback`
                """
            )

def show_single_result(result: LeadOutput):
    st.markdown("---")
    st.subheader(f"⭐ {result.business_name}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Website Status:** {result.website_status}")
        st.markdown(f"**Priority:** {result.priority}")
        st.markdown(f"**Lead Score:** {result.lead_score}")

    with col2:
        st.markdown("**Website Issues:**")
        if result.website_issues:
            for issue in result.website_issues:
                st.write(f"- {issue}")
        else:
            st.write("No major issues found")

    st.markdown("### 📧 Outreach Message")
    st.code(result.outreach_message)


def process_single_lead(user_email: str, lead_data: dict):
    users = load_users()
    # ✅ Inject safe defaults if missing
    if not lead_data.get("category"):
        lead_data["category"] = "Unknown"
    if not lead_data.get("city"):
        lead_data["city"] = "Unknown"
    if not lead_data.get("state"):
        lead_data["state"] = "Unknown"
    if not lead_data.get("email"):
        lead_data["email"] = lead_data.get("contact_email", "") or ""
    try:
        pipeline = LeadQualificationPipeline(OPENAI_API_KEY, offer=get_offer_config())
        lead = LeadInput(**lead_data)
        with st.spinner("⚡ Analyzing website & scoring lead..."):
            result = pipeline.process_lead(lead)

        pipeline.cleanup()

        # ✅ Deduct exactly 1 credit
        users[user_email]["credits"] -= 1
        users[user_email]["total_processed"] += 1
        save_users(users)

        st.session_state.credits = users[user_email]["credits"]

        # Save result
        st.session_state.results.append(result)
        save_results(user_email, st.session_state.results)

        # UI feedback
        st.success("✅ Lead qualified successfully!")
        st.metric("Remaining Credits", st.session_state.credits)

        show_single_result(result)

    except Exception as e:
        st.error("❌ Failed to process lead")
        st.exception(e)


def single_lead_search(user_email):
    st.markdown(
        """
        <div class="comic-panel">
            <h2 style="margin-top: 0;">Single lead</h2>
            <p class="comic-micro" style="margin-top: 0; margin-bottom: 0;">
                Qualify one business using <b>1 credit</b>. Add category/city/state for stronger outreach.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    users = load_users()
    user = users[user_email]

    with st.form("single_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            business_name = st.text_input("Business name*", placeholder="Acme Plumbing")
            website_url = st.text_input("Website URL*", placeholder="https://acme.com")
            category = st.text_input("Category (recommended)", placeholder="Plumbing")
        with col2:
            city = st.text_input("City (recommended)", placeholder="Austin")
            state = st.text_input("State (recommended)", placeholder="TX")
            email = st.text_input("Email (optional)", placeholder="owner@acme.com")

        submitted = st.form_submit_button("Qualify lead")

    if submitted:
        if not business_name or not website_url:
            st.error("❌ Business name and website URL are required")
            return

        if user["credits"] < 1:
            st.error("❌ You don’t have enough credits")
            st.info("💡 Buy more credits to continue")
            return

        process_single_lead(
            user_email=user_email,
            lead_data={
                "business_name": business_name,
                "website_url": website_url,
                "category": category,
                "city": city,
                "state": state,
                "email": email,
            }
        )

def main_app():
    """Main application interface"""
    # Get user info using compatibility functions
    user_email = get_user_email()
    user_name = get_user_name()
    
    # Initialize or get user data
    user_data = get_or_create_user(user_email, user_name)
    st.session_state.credits = user_data['credits']
    
    # Load persona/offer settings once per logged-in user
    if st.session_state.offer_loaded_for != user_email:
        st.session_state.persona = user_data.get("persona", DEFAULT_PERSONA)
        st.session_state.offer_service_label = user_data.get(
            "service_label", PERSONA_PRESETS[DEFAULT_PERSONA]["service_label"]
        )
        st.session_state.offer_offer_line = user_data.get(
            "offer_line", PERSONA_PRESETS[DEFAULT_PERSONA]["offer_line"]
        )
        st.session_state.offer_starting_price = user_data.get(
            "starting_price", PERSONA_PRESETS[DEFAULT_PERSONA]["starting_price"]
        )
        st.session_state.offer_currency_symbol = user_data.get("currency_symbol", DEFAULT_CURRENCY_SYMBOL)
        st.session_state.offer_loaded_for = user_email
        st.session_state.persona_last = st.session_state.persona
    
    # Load previous results
    previous_results = load_results(user_email)
    if previous_results and not st.session_state.results:
        st.session_state.results = [LeadOutput(**r) for r in previous_results]
    
    # Sidebar
    with st.sidebar:
        st.markdown(
            f"""
            <div class="comic-panel">
                <span class="comic-kicker" style="background: var(--comic-secondary);">Workspace</span>
                <h3 style="margin: 0.8rem 0 0 0;">{user_name}</h3>
                <p class="comic-micro" style="margin: 0.2rem 0 0 0;">{user_email}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Credits display
        st.markdown(
            f"""
            <div class="comic-panel" style="text-align: center;">
                <span class="comic-kicker" style="background: var(--comic-primary);">Credits</span>
                <div style="font-family: var(--comic-font-title); font-size: 3rem; margin-top: 0.7rem;">
                    {st.session_state.credits}
                </div>
                <div class="comic-micro" style="margin-top: 0.15rem;">available</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Stats
        users = load_users()
        user_info = users.get(user_email, {})
        
        st.markdown(
            """
            <div class="comic-panel">
                <h3 style="margin-top: 0;">Stats</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Processed", user_info.get("total_processed", 0))
        with col_b:
            st.metric("Plan", user_info.get("subscription", "free").upper())

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="comic-panel">
                <h3 style="margin-top: 0;">Persona & offer</h3>
                <p class="comic-micro" style="margin-top: 0; margin-bottom: 0;">
                    Tailor outreach to your freelancing service.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        persona_options = list(PERSONA_PRESETS.keys())
        persona = st.selectbox("Persona", persona_options, key="persona")
        if persona != st.session_state.persona_last:
            st.session_state.persona_last = persona
            preset = PERSONA_PRESETS.get(persona, PERSONA_PRESETS[DEFAULT_PERSONA])
            if persona != "Custom":
                st.session_state.offer_service_label = preset["service_label"]
                st.session_state.offer_offer_line = preset["offer_line"]
                st.session_state.offer_starting_price = preset["starting_price"]

        st.number_input("Starting price", min_value=0, step=1, key="offer_starting_price")
        with st.expander("Customize wording", expanded=False):
            st.text_input("Service label", key="offer_service_label", placeholder="e.g., web development")
            st.text_input("Offer line", key="offer_offer_line", placeholder="e.g., Professional websites")
            st.text_input("Currency symbol", key="offer_currency_symbol", max_chars=3)

        if st.button("Save persona & offer", width="stretch"):
            users = load_users()
            if user_email in users:
                users[user_email]["persona"] = st.session_state.persona
                users[user_email]["service_label"] = st.session_state.offer_service_label
                users[user_email]["offer_line"] = st.session_state.offer_offer_line
                users[user_email]["starting_price"] = st.session_state.offer_starting_price
                users[user_email]["currency_symbol"] = st.session_state.offer_currency_symbol
                save_users(users)
                st.success("Saved.")
        
        st.markdown("---")
        
        # Logout button
        if st.button("Logout", width="stretch"):
            try:
                st.logout()
            except:
                # Fallback logout for non-authenticated mode
                st.session_state.logged_in = False
                st.session_state.user_email = None
                st.session_state.user_name = None
            st.rerun()

    
    # Main content
    st.markdown(
        f"""
        <div class="comic-hero">
            <span class="comic-kicker" style="background: var(--comic-secondary);">Dashboard</span>
            <h1 style="margin-top: 0.75rem; margin-bottom: 0.25rem;">Lead Qualifier Pro</h1>
            <p class="comic-subtitle">
                Upload leads, scan websites, and generate outreach drafts — then export and start contacting.
            </p>
            <div style="margin-top: 0.85rem;">
                <span class="comic-badge comic-badge--good">{st.session_state.credits} credits</span>
                <span class="comic-badge comic-badge--alt">{len(st.session_state.results)} saved results</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    #tabs
    tab1 ,tab2, tab3, tab4, tab5 = st.tabs(
    ["Home", "Upload Leads", "Single Lead", "Results", "Credits"]
 )
    with tab1:
        st.markdown(
            """
            <div class="comic-panel">
                <h2 style="margin-top: 0;">Qualify business leads in minutes</h2>
                <p class="comic-micro" style="margin-top: 0;">
                    This app turns a lead list into a prioritized queue with clear reasons and ready-to-send outreach drafts.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(
                """
                <div class="comic-panel">
                    <h3 style="margin-top: 0;">1) Upload</h3>
                    <p class="comic-micro" style="margin-top: 0;">
                        Drop in a CSV lead list and preview the first rows before processing.
                    </p>
                    <span class="comic-badge comic-badge--warn">1 credit / lead</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                """
                <div class="comic-panel">
                    <h3 style="margin-top: 0;">2) Prioritize</h3>
                    <p class="comic-micro" style="margin-top: 0;">
                        Get a score, priority tier, and website issues you can reference in outreach.
                    </p>
                    <span class="comic-badge comic-badge--good">High-value first</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_c:
            st.markdown(
                """
                <div class="comic-panel">
                    <h3 style="margin-top: 0;">3) Export</h3>
                    <p class="comic-micro" style="margin-top: 0;">
                        Download Excel/CSV/JSON and start contacting right away.
                    </p>
                    <span class="comic-badge comic-badge--alt">Team-friendly</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="comic-panel">
                <h3 style="margin-top: 0;">Works for more than web dev</h3>
                <p class="comic-micro" style="margin-top: 0;">
                    Use the same lead qualification workflow across different freelancing services:
                </p>
                <div>
                    <span class="comic-badge comic-badge--alt">Sales outreach</span>
                    <span class="comic-badge comic-badge--alt">Editors / copywriters</span>
                    <span class="comic-badge comic-badge--alt">Video editors</span>
                    <span class="comic-badge comic-badge--alt">Designers</span>
                    <span class="comic-badge comic-badge--alt">SEO consultants</span>
                </div>
                <p class="comic-micro" style="margin-bottom: 0;">
                    Set your persona and offer in the sidebar (so outreach reflects your service).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="comic-panel">
                <h3 style="margin-top: 0;">Support & privacy</h3>
                <p class="comic-micro" style="margin-top: 0; margin-bottom: 0;">
                    Your data stays in your workspace. For help, email: leadqualifierhelp28@gmail.com
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    
    with tab2:
        upload_section(user_email)
    
    with tab3:
        single_lead_search(user_email)

    with tab4:
        results_section()
    
    with tab5:
        credits_section(user_email)


def upload_section(user_email):
    """Upload and processing section"""
    st.markdown(
        """
        <div class="comic-panel">
            <h2 style="margin-top: 0;">Upload your lead list</h2>
            <p class="comic-micro" style="margin-top: 0; margin-bottom: 0;">
                Upload a CSV and we’ll qualify each business by website signals, lead score, and priority.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    with st.expander("CSV format", expanded=False):
        st.markdown(
            """
            **Required**
            - `business_name`
            - `website_url` (include `http://` or `https://` when possible)

            **Recommended (improves scoring/outreach)**
            - `category`
            - `city`
            - `state`

            **Optional**
            - `email` (or `contact_email`)

            **Example**
            ```
            business_name,website_url,category,city,state,email
            Acme Plumbing,https://acme.com,Plumbing,Austin,TX,owner@acme.com
            Bright Dental,https://brightdental.com,Dentist,Miami,FL,
            ```
            """
        )
        
        # Sample CSV download
        sample_data = {
            "business_name": ["Acme Plumbing", "Bright Dental", "Sunset Landscaping"],
            "website_url": ["https://acme.com", "https://brightdental.com", ""],
            "category": ["Plumbing", "Dentist", "Landscaping"],
            "city": ["Austin", "Miami", "Dallas"],
            "state": ["TX", "FL", "TX"],
            "email": ["owner@acme.com", "", "info@sunset.com"],
        }
        sample_df = pd.DataFrame(sample_data)
        sample_csv = sample_df.to_csv(index=False)
        
        st.download_button(
            label="Download sample CSV",
            data=sample_csv,
            file_name="sample_leads.csv",
            mime="text/csv",
            width="stretch"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file containing your lead information"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            original_columns = set(df.columns)
             
            # Validate required columns
            required_cols = ['business_name', 'website_url']
            missing_cols = [col for col in required_cols if col not in df.columns]
             
            if missing_cols:
                st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                return
             
            # Normalize missing values
            df = df.fillna("")

            # Optional columns (keep CSV flexible)
            if "category" not in df.columns:
                df["category"] = "Unknown"
            if "city" not in df.columns:
                df["city"] = "Unknown"
            if "state" not in df.columns:
                df["state"] = "Unknown"
            if "contact_name" not in df.columns:
                df["contact_name"] = ""
            if "contact_email" not in df.columns:
                df["contact_email"] = ""
            if "email" not in df.columns:
                df["email"] = df["contact_email"] if "contact_email" in df.columns else ""

            # If email is blank but contact_email is present, copy it over
            df.loc[(df["email"] == "") & (df["contact_email"] != ""), "email"] = df["contact_email"]

            # Normalize blanks for recommended fields
            for col in ["category", "city", "state"]:
                df[col] = df[col].astype(str).str.strip()
                df.loc[df[col] == "", col] = "Unknown"

            missing_recommended = [c for c in ["category", "city", "state"] if c not in original_columns]
            if missing_recommended:
                st.warning(
                    "Recommended columns missing (we’ll still run): "
                    + ", ".join(missing_recommended)
                )
             
            # Preview
            st.success(f"✅ File loaded successfully! Found {len(df)} leads")
            
            with st.expander("👀 Preview Data", expanded=True):
                st.dataframe(df.head(10), width=None)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Processing section
            col1, col2 = st.columns([2, 1])
            
            with col1:
                num_leads = len(df)
                st.info(f"""
                **📊 Processing Summary:**
                - {num_leads} leads to process
                - {num_leads} credit(s) will be used
                - {st.session_state.credits} credit(s) available
                """)
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                
                if num_leads > st.session_state.credits:
                    st.error(f"❌ Insufficient credits! You need {num_leads} credits but only have {st.session_state.credits}")
                    st.info("💡 Purchase more credits to continue")
                else:
                    if st.button("🚀 Process Leads", type="primary", width="stretch"):
                        process_leads(df, user_email, num_leads)
        
        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")
            st.info("💡 Make sure your CSV has the required columns")


def process_leads(df, user_email, num_leads):
    """Process leads through qualification pipeline"""
    try:
        pipeline = LeadQualificationPipeline(OPENAI_API_KEY, offer=get_offer_config())
        leads = [LeadInput(**row) for _, row in df.iterrows()]
        
        results = []
        total = len(leads)
        
        # Progress indicators
        st.markdown("<br>", unsafe_allow_html=True)
        st.header("⚡ Processing Your Leads...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        result_preview = st.empty()
        
        for idx, lead in enumerate(leads):
            status_text.markdown(f"""
            <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 1rem; border-radius: 0.5rem; text-align: center;'>
                ⚡ Processing {idx + 1}/{total}: <strong>{lead.business_name}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                result = pipeline.process_lead(lead)
                results.append(result)
                
                if result.priority == 'HIGH':
                    result_preview.success(f"🔥 HIGH Priority: {lead.business_name}")
            
            except Exception as e:
                st.warning(f"⚠️ Error processing {lead.business_name}: {e}")
                results.append(LeadOutput(
                    business_name=lead.business_name,
                    website_status="Error",
                    website_issues=[str(e)],
                    lead_score=0,
                    priority="LOW",
                    outreach_message="Processing failed"
                ))
            
            progress_bar.progress((idx + 1) / total)
        
        status_text.markdown("""
        <div style='background: #d4edda; color: #155724; padding: 1.5rem; 
                    border-radius: 0.5rem; text-align: center; font-size: 1.2rem; font-weight: bold;'>
            ✅ Processing Complete!
        </div>
        """, unsafe_allow_html=True)
        
        pipeline.cleanup()
        
        # Update user credits
        users = load_users()
        users[user_email]['credits'] -= num_leads
        users[user_email]['total_processed'] += num_leads
        save_users(users)
        st.session_state.credits = users[user_email]['credits']
        
        # Save results
        st.session_state.results.extend(results)
        save_results(user_email, st.session_state.results)
        
        # Display results
        display_results(results, num_leads, user_email, users)
        
        st.balloons()
    
    except Exception as e:
        st.error(f"❌ Processing Error: {str(e)}")
        import traceback
        with st.expander("🔍 Show technical details"):
            st.code(traceback.format_exc())


def display_results(results, num_leads, user_email, users):
    """Display processing results"""
    st.header("Results and insights")
    
    high_priority = sum(1 for r in results if r.priority == 'HIGH')
    medium_priority = sum(1 for r in results if r.priority == 'MEDIUM')
    low_priority = sum(1 for r in results if r.priority == 'LOW')
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total leads", len(results))
    with col2:
        st.metric("High priority", high_priority)
    with col3:
        st.metric("Medium priority", medium_priority)
    with col4:
        st.metric("Low priority", low_priority)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Results table
    results_data = [r.model_dump() for r in results]
    df_results = pd.DataFrame(results_data)
    df_results['website_issues'] = df_results['website_issues'].apply(
        lambda x: '; '.join(x) if x else ''
    )
    
    st.subheader("All results")
    st.dataframe(df_results, width=None, height=300)
    
    # High priority leads detail
    if high_priority > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("High-priority leads (ready to contact)")
        
        high_df = df_results[df_results['priority'] == 'HIGH']
        
        for idx, row in high_df.iterrows():
            with st.expander(
                f"⭐ {row['business_name']} (Score: {row['lead_score']}) - {row['website_status']}",
                expanded=(idx == high_df.index[0])
            ):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Status:** {row['website_status']}")
                    st.markdown(f"**Issues:** {row['website_issues']}")
                with col2:
                    st.markdown(f"**Score:** {row['lead_score']}")
                    st.markdown(f"**Priority:** {row['priority']}")
                
                st.markdown("**📧 Outreach Message:**")
                st.info(row['outreach_message'])
                st.code(row['outreach_message'], language=None)
    
    # Download section
    st.markdown("<br>", unsafe_allow_html=True)
    st.header("Download results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        excel_data = convert_df_to_excel(df_results)
        st.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name=f"qualified_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )
    
    with col2:
        csv_data = df_results.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"qualified_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch"
        )
    
    with col3:
        json_data = json.dumps(results_data, indent=2)
        st.download_button(
            label="📦 Download JSON",
            data=json_data,
            file_name=f"qualified_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width="stretch"
        )
    
    # Success message
    st.markdown("<br>", unsafe_allow_html=True)
    st.success(f"""
    ✅ **Processing Complete!**
    - {num_leads} credits used
    - {users[user_email]['credits']} credits remaining
    - {high_priority} high-priority leads ready to contact
    """)


def results_section():
    """Results viewing section"""
    st.markdown(
        """
        <div class="comic-panel">
            <h2 style="margin-top: 0;">Results</h2>
            <p class="comic-micro" style="margin-top: 0; margin-bottom: 0;">
                Your saved leads, scores, and outreach drafts.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not st.session_state.results:
        st.info("No results yet. Upload and process leads in the 'Upload Leads' tab!")
        return
    
    # Calculate metrics
    high, medium, low, avg_score = calculate_priority_metrics(st.session_state.results)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Leads", len(st.session_state.results))
    with col2:
        st.metric("HIGH Priority", high)
    with col3:
        st.metric("MEDIUM Priority", medium)
    with col4:
        st.metric("Avg Score", f"{avg_score:.1f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Results table
    results_data = [r.model_dump() for r in st.session_state.results]
    df_results = pd.DataFrame(results_data)
    df_results['website_issues'] = df_results['website_issues'].apply(
        lambda x: '; '.join(x) if x else ''
    )
    
    st.dataframe(df_results, width='stretch', height=400)
    
    # Download buttons
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        excel_data = convert_df_to_excel(df_results)
        st.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name=f"all_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )
    
    with col2:
        csv_data = df_results.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"all_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch"
        )
    
    with col3:
        json_data = json.dumps(results_data, indent=2)
        st.download_button(
            label="📦 Download JSON",
            data=json_data,
            file_name=f"all_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width="stretch"
        )


def credits_section(user_email):
    """Credits management section"""
    st.markdown(
        """
        <div class="comic-panel">
            <h2 style="margin-top: 0;">Credits</h2>
            <p class="comic-micro" style="margin-top: 0; margin-bottom: 0;">
                Credits power lead processing. <b>1 qualified lead = 1 credit</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    users = load_users()
    user_info = users.get(user_email, {})
    
    # Current balance
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="comic-hero" style="text-align: center;">
            <span class="comic-kicker" style="background: var(--comic-primary);">Balance</span>
            <div style="font-family: var(--comic-font-title); font-size: 4rem; margin-top: 0.9rem;">
                {user_info.get("credits", 0)}
            </div>
            <p class="comic-subtitle" style="margin-top: 0.2rem; margin-bottom: 0;">
                credits available
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Usage stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Processed", user_info.get('total_processed', 0))
    with col2:
        st.metric("Subscription Plan", user_info.get('subscription', 'free').upper())
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Credit packages
    st.subheader("Purchase credits")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div class="comic-panel" style="text-align: center;">
                <span class="comic-kicker" style="background: var(--comic-secondary);">Starter</span>
                <h2 style="margin-top: 0.9rem; margin-bottom: 0.25rem;">50 credits</h2>
                <div style="font-family: var(--comic-font-title); font-size: 2.2rem;">$49</div>
                <p class="comic-micro" style="margin-bottom: 0;">Perfect for solo sprints</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Buy Starter", width="stretch"):
            st.info("Payment integration coming soon!")
    
    with col2:
        st.markdown(
            """
            <div class="comic-panel" style="text-align: center;">
                <span class="comic-kicker" style="background: var(--comic-primary);">Professional</span>
                <h2 style="margin-top: 0.9rem; margin-bottom: 0.25rem;">200 credits</h2>
                <div style="font-family: var(--comic-font-title); font-size: 2.2rem;">$149</div>
                <p class="comic-micro" style="margin-bottom: 0;">Best for weekly outreach</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Buy Professional", width="stretch"):
            st.info("Payment integration coming soon!")
    
    with col3:
        st.markdown(
            """
            <div class="comic-panel" style="text-align: center;">
                <span class="comic-kicker" style="background: var(--comic-danger);">Enterprise</span>
                <h2 style="margin-top: 0.9rem; margin-bottom: 0.25rem;">1000 credits</h2>
                <div style="font-family: var(--comic-font-title); font-size: 2.2rem;">$499</div>
                <p class="comic-micro" style="margin-bottom: 0;">Built for teams at scale</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Buy Enterprise", width="stretch"):
            st.info("Payment integration coming soon!")


def main():
    init_session_state()

    if not is_user_logged_in():
        login_page()
        st.stop()

    main_app()


if __name__ == "__main__":
    main()

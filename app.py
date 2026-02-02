import streamlit as st
import pandas as pd
import json
from io import BytesIO
import os
from datetime import datetime
import hashlib
import sys

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.website_inspector import WebsiteInspector
from src.agents.website_classifier import WebsiteClassifier
from src.agents.lead_scorer import LeadScorer
from src.agents.outreach_generator import OutreachGenerator
from src.models.schemas import LeadInput, LeadOutput

st.set_page_config(
    page_title="Lead Qualifier Pro - AI Lead Qualification",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

RESULTS_DIR = "data/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") or st.secrets.get("OPENAI_API_KEY", "")

# Payment Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
STRIPE_KEY = os.getenv("STRIPE_KEY", "")

USER_DB_FILE = "users.json"


class LeadQualificationPipeline:
    def __init__(self, OPENAI_API_KEY: str):
        self.inspector = WebsiteInspector()
        self.classifier = WebsiteClassifier()
        self.scorer = LeadScorer()
        self.outreach_gen = OutreachGenerator(api_key=OPENAI_API_KEY)
    
    def process_lead(self, lead: LeadInput) -> LeadOutput:
        inspection = self.inspector.inspect(lead.website_url)
        classification = self.classifier.classify(inspection)
        scoring = self.scorer.score(lead, classification)
        
        if scoring.priority.value in ['HIGH', 'MEDIUM']:
            outreach = self.outreach_gen.generate(lead, classification, scoring)
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
    
    if email not in users:
        users[email] = {
            'email': email,
            'name': name or email.split('@')[0],
            'credits': 10,  # Free trial credits
            'total_processed': 0,
            'created_at': datetime.now().isoformat(),
            'subscription': 'free'
        }
        save_users(users)
    
    return users[email]


def init_session_state():
    """Initialize session state variables"""
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'credits' not in st.session_state:
        st.session_state.credits = 0


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
    st.markdown("""
        <div style='text-align: center; padding: 3rem 0;'>
            <h1>🎯 Lead Qualifier Pro</h1>
            <p>AI-Powered Lead Qualification</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.info("Sign in with Google to continue")

    if st.button("🔐 Sign in with Google", type="primary", width="stretch"):
        try:
            st.login()
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            st.info("""
            **For Streamlit Cloud deployment:**
            
            Update your `.streamlit/secrets.toml` with your app URL:
            
            ```toml
            [auth]
            redirect_uri = "https://your-app-name.streamlit.app/oauth2callback"
            cookie_secret = "your-secret"
            client_id = "your-google-client-id"
            client_secret = "your-google-client-secret"
            server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
            ```
            
            Also update your Google OAuth redirect URI to match your Streamlit Cloud URL.
            """)

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
    lead_data.setdefault("category", "Unknown")
    lead_data.setdefault("city", "Unknown")
    lead_data.setdefault("state", "Unknown")
    try:
        pipeline = LeadQualificationPipeline(OPENAI_API_KEY)
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
    st.markdown("### 🔍 Single Lead Search")
    st.caption("Search and qualify one lead using **1 credit**")

    users = load_users()
    user = users[user_email]

    with st.form("single_lead_form"):
        business_name = st.text_input("Business Name*", placeholder="Acme Corp")
        website_url = st.text_input(
            "Website URL*",
            placeholder="https://acme.com"
        )
        contact_name = st.text_input("Contact Name (optional)")
        contact_email = st.text_input("Contact Email (optional)")

        submitted = st.form_submit_button("🚀 Qualify Lead")

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
                "contact_name": contact_name,
                "contact_email": contact_email,
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
    
    # Load previous results
    previous_results = load_results(user_email)
    if previous_results and not st.session_state.results:
        st.session_state.results = [LeadOutput(**r) for r in previous_results]
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       padding: 1.5rem; border-radius: 0.5rem; text-align: center; color: white;'>
                <h3 style='margin: 0;'>👤 {user_name}</h3>
                <p style='margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;'>{user_email}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Credits display
        st.markdown(f"""
            <div style='background: #f0f2f6; padding: 1rem; border-radius: 0.5rem; text-align: center;'>
                <h2 style='color: #667eea; margin: 0;'>{st.session_state.credits}</h2>
                <p style='color: #666; margin: 0.5rem 0 0 0;'>Credits Available</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Stats
        users = load_users()
        user_info = users.get(user_email, {})
        
        st.markdown("### 📊 Your Stats")
        st.metric("Total Processed", user_info.get('total_processed', 0))
        st.metric("Subscription", user_info.get('subscription', 'free').upper())
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", width="stretch"):
            try:
                st.logout()
            except:
                # Fallback logout for non-authenticated mode
                st.session_state.logged_in = False
                st.session_state.user_email = None
                st.session_state.user_name = None
            st.rerun()

    
    # Main content
    st.markdown("""🎯
        <h1 style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
             Lead Qualifier Pro
        </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <p style='text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 2rem;'>
            Upload your leads, and we'll analyze their websites to help you prioritize outreach
        </p>
    """, unsafe_allow_html=True)
    
    #tabs
    tab1, tab2, tab3, tab4 = st.tabs(
    ["📤 Upload Leads", "🔍 Single Lead Search", "📊 Results", "💳 Credits"]
)

    
    with tab1:
        upload_section(user_email)
    
    with tab2:
        single_lead_search(user_email)

    with tab3:
        results_section()
    
    with tab4:
        credits_section(user_email)


def upload_section(user_email):
    """Upload and processing section"""
    st.markdown("### Upload Your Lead List")
    
    with st.expander("📋 CSV Format Requirements", expanded=False):
        st.markdown("""
        Your CSV file should have the following columns:
        - `business_name` - Company name
        - `website_url` - Full website URL (including http:// or https://)
        - `contact_name` - Contact person's name (optional)
        - `contact_email` - Contact person's email (optional)
        
        **Example:**
        ```
        business_name,website_url,contact_name,contact_email
        Acme Corp,https://acme.com,John Doe,john@acme.com
        Tech Solutions,https://techsolutions.io,Jane Smith,jane@techsolutions.io
        ```
        """)
        
        # Sample CSV download
        sample_data = {
            'business_name': ['Acme Corp', 'Tech Solutions', 'Digital Agency'],
            'website_url': ['https://acme.com', 'https://techsolutions.io', 'https://digitalagency.co'],
            'contact_name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'contact_email': ['john@acme.com', 'jane@techsolutions.io', 'bob@digitalagency.co']
        }
        sample_df = pd.DataFrame(sample_data)
        sample_csv = sample_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Sample CSV",
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
            
            # Validate required columns
            required_cols = ['business_name', 'website_url']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                return
            
            # Fill optional columns
            if 'contact_name' not in df.columns:
                df['contact_name'] = ''
            if 'contact_email' not in df.columns:
                df['contact_email'] = ''
            
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
        pipeline = LeadQualificationPipeline(api_key=OPENAI_API_KEY)
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
    st.header("📊 Results & Insights")
    
    high_priority = sum(1 for r in results if r.priority == 'HIGH')
    medium_priority = sum(1 for r in results if r.priority == 'MEDIUM')
    low_priority = sum(1 for r in results if r.priority == 'LOW')
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='border-left: 4px solid #667eea; padding: 1rem; background: #f8f9fa;'>
            <h2 style='color: #667eea; margin: 0;'>{len(results)}</h2>
            <p style='color: #666; margin: 0;'>Total Leads</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='border-left: 4px solid #e74c3c; padding: 1rem; background: #f8f9fa;'>
            <h2 style='color: #e74c3c; margin: 0;'>🔥 {high_priority}</h2>
            <p style='color: #666; margin: 0;'>HIGH Priority</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='border-left: 4px solid #f39c12; padding: 1rem; background: #f8f9fa;'>
            <h2 style='color: #f39c12; margin: 0;'>📊 {medium_priority}</h2>
            <p style='color: #666; margin: 0;'>MEDIUM Priority</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style='border-left: 4px solid #95a5a6; padding: 1rem; background: #f8f9fa;'>
            <h2 style='color: #95a5a6; margin: 0;'>📉 {low_priority}</h2>
            <p style='color: #666; margin: 0;'>LOW Priority</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Results table
    results_data = [r.model_dump() for r in results]
    df_results = pd.DataFrame(results_data)
    df_results['website_issues'] = df_results['website_issues'].apply(
        lambda x: '; '.join(x) if x else ''
    )
    
    st.subheader("📋 All Results")
    st.dataframe(df_results, width=None, height=300)
    
    # High priority leads detail
    if high_priority > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🔥 HIGH Priority Leads - Ready to Contact!")
        
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
    st.header("💾 Download Your Results")
    
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
    st.markdown("### 📊 Your Previous Results")
    
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
    st.markdown("### 💳 Manage Your Credits")
    
    users = load_users()
    user_info = users.get(user_email, {})
    
    # Current balance
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   padding: 2rem; border-radius: 1rem; text-align: center; color: white; margin-bottom: 2rem;'>
            <h1 style='margin: 0; font-size: 3rem;'>{user_info.get('credits', 0)}</h1>
            <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem;'>Available Credits</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Usage stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Processed", user_info.get('total_processed', 0))
    with col2:
        st.metric("Subscription Plan", user_info.get('subscription', 'free').upper())
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Credit packages
    st.subheader("💰 Purchase Credits")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='border: 2px solid #667eea; border-radius: 0.5rem; padding: 1.5rem; text-align: center;'>
                <h3 style='color: #667eea;'>Starter</h3>
                <h2>50 Credits</h2>
                <p style='font-size: 1.5rem; color: #667eea;'>$49</p>
                <p style='color: #666;'>Perfect for small teams</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Buy Starter", width="stretch"):
            st.info("Payment integration coming soon!")
    
    with col2:
        st.markdown("""
            <div style='border: 2px solid #764ba2; border-radius: 0.5rem; padding: 1.5rem; text-align: center;'>
                <h3 style='color: #764ba2;'>Professional</h3>
                <h2>200 Credits</h2>
                <p style='font-size: 1.5rem; color: #764ba2;'>$149</p>
                <p style='color: #666;'>Most popular choice</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Buy Professional", width="stretch"):
            st.info("Payment integration coming soon!")
    
    with col3:
        st.markdown("""
            <div style='border: 2px solid #e74c3c; border-radius: 0.5rem; padding: 1.5rem; text-align: center;'>
                <h3 style='color: #e74c3c;'>Enterprise</h3>
                <h2>1000 Credits</h2>
                <p style='font-size: 1.5rem; color: #e74c3c;'>$499</p>
                <p style='color: #666;'>Best value for scale</p>
            </div>
        """, unsafe_allow_html=True)
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
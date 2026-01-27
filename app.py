import streamlit as st
import pandas as pd
import json
from io import BytesIO
import os
from datetime import datetime
import hashlib

from src.agents.website_inspector import WebsiteInspector
from src.agents.website_classifier import WebsiteClassifier
from src.agents.lead_scorer import LeadScorer
from src.agents.outreach_generator import OutreachGenerator
from src.models.schemas import LeadInput, LeadOutput

# Page config
st.set_page_config(
    page_title="Lead Qualifier Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Your API key (set this in Streamlit Cloud secrets or .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Simple user database (replace with real DB in production)
# Format: {email: {password_hash, credits, total_processed}}
USER_DB_FILE = "users.json"

def load_users():
    """Load user database"""
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save user database"""
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_session_state():
    """Initialize session state"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'credits' not in st.session_state:
        st.session_state.credits = 0

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(120deg, #1f77b4, #2ecc71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 1.2rem;
    }
    .pricing-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .credit-badge {
        background: #2ecc71;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: bold;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


class LeadQualificationPipeline:
    """Pipeline for processing leads"""
    
    def __init__(self, api_key: str):
        self.inspector = WebsiteInspector()
        self.classifier = WebsiteClassifier()
        self.scorer = LeadScorer()
        self.outreach_gen = OutreachGenerator(api_key=api_key)
    
    def process_lead(self, lead: LeadInput) -> LeadOutput:
        inspection = self.inspector.inspect(lead.website_url)
        classification = self.classifier.classify(inspection)
        scoring = self.scorer.score(lead, classification)
        
        if scoring.priority.value in ['HIGH', 'MEDIUM']:
            outreach = self.outreach_gen.generate(lead, classification)
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


def convert_df_to_excel(df):
    """Convert DataFrame to Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Qualified Leads')
    return output.getvalue()


def login_page():
    """Login/Signup page"""
    st.markdown('<p class="main-header">🎯 Lead Qualifier Pro</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Lead Qualification for Freelancers</p>', unsafe_allow_html=True)
    
    # Value proposition
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3>⚡ Instant Qualification</h3>
            <p>Upload CSV, get qualified leads in seconds</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3>🤖 AI-Powered</h3>
            <p>Smart outreach messages for each lead</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-box">
            <h3>💰 Pay As You Go</h3>
            <p>No subscription, just buy credits</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Login/Signup tabs
    tab1, tab2 = st.tabs(["🔐 Login", "✨ Sign Up (Free Trial)"])
    
    users = load_users()
    
    with tab1:
        st.subheader("Welcome Back!")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True):
            if email in users and users[email]['password'] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.credits = users[email]['credits']
                st.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid email or password")
    
    with tab2:
        st.subheader("Start Your Free Trial")
        st.info("🎁 Get 10 FREE credits to try it out (no credit card required)")
        
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Sign Up & Get 10 Free Credits", use_container_width=True):
            if not new_email or not new_password:
                st.error("❌ Please fill all fields")
            elif new_password != confirm_password:
                st.error("❌ Passwords don't match")
            elif new_email in users:
                st.error("❌ Email already registered")
            else:
                users[new_email] = {
                    'password': hash_password(new_password),
                    'credits': 10,  # FREE TRIAL
                    'total_processed': 0,
                    'created_at': datetime.now().isoformat()
                }
                save_users(users)
                
                st.session_state.logged_in = True
                st.session_state.user_email = new_email
                st.session_state.credits = 10
                
                st.success("🎉 Account created! You have 10 free credits!")
                st.balloons()
                st.rerun()
    
    # Pricing section
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("💳 Pricing")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <h3>Starter</h3>
            <h1>$10</h1>
            <p>50 credits</p>
            <p style='font-size: 0.9em;'>$0.20 per lead</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="pricing-card">
            <h3>Pro ⭐</h3>
            <h1>$35</h1>
            <p>200 credits</p>
            <p style='font-size: 0.9em;'>$0.175 per lead</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="pricing-card">
            <h3>Agency</h3>
            <h1>$80</h1>
            <p>500 credits</p>
            <p style='font-size: 0.9em;'>$0.16 per lead</p>
        </div>
        """, unsafe_allow_html=True)


def main_app():
    """Main application for logged-in users"""
    users = load_users()
    user_email = st.session_state.user_email
    user_data = users[user_email]
    
    # Header with credits
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<p class="main-header">🎯 Lead Qualifier Pro</p>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="credit-badge">💳 {user_data["credits"]} Credits</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user_email}")
        st.metric("Available Credits", user_data['credits'])
        st.metric("Total Processed", user_data['total_processed'])
        
        st.markdown("---")
        
        if st.button("💰 Buy More Credits"):
            st.info("""
            **Purchase Credits:**
            - 50 credits: $10
            - 200 credits: $35 (Save 12%)
            - 500 credits: $80 (Save 20%)
            
            Contact: support@leadqualifier.com
            """)
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.credits = 0
            st.rerun()
        
        st.markdown("---")
        
        # Download sample
        sample_data = {
            'business_name': ['Joe\'s Plumbing', 'Tech Solutions', 'Maria\'s Landscaping'],
            'category': ['Plumbing', 'IT Services', 'Landscaping'],
            'city': ['Austin', 'Dallas', 'Houston'],
            'state': ['TX', 'TX', 'TX'],
            'website_url': ['', 'https://techsolutions.com', 'http://mariaslandscape.com'],
            'email': ['joe@gmail.com', 'contact@techsolutions.com', 'maria@yahoo.com']
        }
        sample_df = pd.DataFrame(sample_data)
        csv = sample_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Sample CSV",
            data=csv,
            file_name="sample_leads.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Check if API key is configured
    if not OPENAI_API_KEY:
        st.error("⚠️ Service temporarily unavailable. Please contact support.")
        return
    
    # Main workflow
    st.header("1️⃣ Upload Your Leads")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Required columns: business_name, category, city, state, website_url, email"
    )
    
    if uploaded_file is not None:
        try:
            df_preview = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)
            
            num_leads = len(df_preview)
            
            st.success(f"✅ Loaded {num_leads} leads")
            
            with st.expander("👀 Preview"):
                st.dataframe(df_preview.head(10))
            
            # Cost calculation
            st.header("2️⃣ Review & Process")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Leads to Process", num_leads)
            with col2:
                st.metric("Credits Required", num_leads)
            with col3:
                remaining = user_data['credits'] - num_leads
                st.metric("Credits After", remaining)
            
            # Check if enough credits
            if user_data['credits'] < num_leads:
                st.error(f"❌ Insufficient credits! You need {num_leads} but only have {user_data['credits']}")
                st.info("💡 Buy more credits from the sidebar")
                return
            
            # Process button
            if st.button("🚀 Process Leads", type="primary", use_container_width=True):
                try:
                    # Initialize pipeline
                    with st.spinner("Initializing AI agents..."):
                        pipeline = LeadQualificationPipeline(api_key=OPENAI_API_KEY)
                    
                    # Load leads
                    leads = []
                    df_input = pd.read_csv(uploaded_file)
                    df_input['website_url'] = df_input['website_url'].fillna('')
                    df_input['email'] = df_input['email'].fillna('')
                    
                    for _, row in df_input.iterrows():
                        try:
                            lead = LeadInput(**row.to_dict())
                            leads.append(lead)
                        except Exception as e:
                            st.warning(f"⚠️ Skipped invalid row: {e}")
                    
                    if not leads:
                        st.error("❌ No valid leads found")
                        return
                    
                    # Process with progress
                    st.header("3️⃣ Processing...")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = []
                    for idx, lead in enumerate(leads):
                        status_text.text(f"Processing {idx + 1}/{len(leads)}: {lead.business_name}")
                        
                        try:
                            result = pipeline.process_lead(lead)
                            results.append(result)
                        except Exception as e:
                            st.warning(f"⚠️ Error: {lead.business_name}")
                            results.append(LeadOutput(
                                business_name=lead.business_name,
                                website_status="Error",
                                website_issues=[str(e)],
                                lead_score=0,
                                priority="LOW",
                                outreach_message="Processing failed"
                            ))
                        
                        progress_bar.progress((idx + 1) / len(leads))
                    
                    status_text.text("✅ Complete!")
                    pipeline.cleanup()
                    
                    # Deduct credits
                    users[user_email]['credits'] -= num_leads
                    users[user_email]['total_processed'] += num_leads
                    save_users(users)
                    st.session_state.credits = users[user_email]['credits']
                    
                    # Results
                    st.header("4️⃣ Results")
                    
                    high = sum(1 for r in results if r.priority == 'HIGH')
                    medium = sum(1 for r in results if r.priority == 'MEDIUM')
                    low = sum(1 for r in results if r.priority == 'LOW')
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total", len(results))
                    col2.metric("🔥 HIGH", high)
                    col3.metric("📊 MEDIUM", medium)
                    col4.metric("📉 LOW", low)
                    
                    # DataFrame
                    results_data = [r.model_dump() for r in results]
                    df_results = pd.DataFrame(results_data)
                    df_results['website_issues'] = df_results['website_issues'].apply(
                        lambda x: '; '.join(x) if x else ''
                    )
                    
                    st.dataframe(df_results, use_container_width=True)
                    
                    # High priority
                    if high > 0:
                        st.subheader("🔥 HIGH Priority - Ready to Contact")
                        high_df = df_results[df_results['priority'] == 'HIGH']
                        
                        for idx, row in high_df.iterrows():
                            with st.expander(f"⭐ {row['business_name']} (Score: {row['lead_score']})"):
                                st.write(f"**Status:** {row['website_status']}")
                                st.write(f"**Issues:** {row['website_issues']}")
                                st.info(row['outreach_message'])
                    
                    # Download
                    st.header("5️⃣ Download")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        excel = convert_df_to_excel(df_results)
                        st.download_button(
                            "📊 Download Excel",
                            excel,
                            "qualified_leads.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    with col2:
                        csv = df_results.to_csv(index=False)
                        st.download_button(
                            "📄 Download CSV",
                            csv,
                            "qualified_leads.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    st.success(f"✅ {num_leads} credits deducted. Remaining: {users[user_email]['credits']}")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Details"):
                        st.code(traceback.format_exc())
        
        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")


def main():
    """Main entry point"""
    init_session_state()
    
    if st.session_state.logged_in:
        main_app()
    else:
        login_page()


if __name__ == "__main__":
    main()
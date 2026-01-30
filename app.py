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

st.set_page_config(
    page_title="Lead Qualifier Pro - AI Lead Qualification",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

RESULTS_DIR = "data/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

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

def is_user_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


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
    """Display login page with OIDC authentication"""
    st.markdown("""
        <div style='text-align: center; padding: 3rem 0;'>
            <h1 style='font-size: 3rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                🎯 Lead Qualifier Pro
            </h1>
            <p style='font-size: 1.2rem; color: #666; margin-top: 1rem;'>
                AI-Powered Lead Qualification & Outreach Generation
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       padding: 2rem; border-radius: 1rem; text-align: center; color: white;'>
                <h3 style='margin: 0 0 1rem 0;'>🚀 Get Started</h3>
                <p style='margin: 0 0 1.5rem 0; opacity: 0.9;'>
                    Sign in to start qualifying leads with AI
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Login button
        if st.button("🔐 Continue", use_container_width=True, type="primary"):
               st.session_state["logged_in"] = True
               st.rerun()

        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.info("""
            **✨ What you get:**
            - 10 free credits to start
            - AI-powered lead qualification
            - Automated outreach message generation
            - Export results to Excel, CSV, or JSON
        """)


def main_app():
    """Main application interface"""
    # Get user info from st.user
    user_email = st.user.get('email', 'unknown@example.com')
    user_name = st.user.get('name', 'User')
    
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
        if st.button("🚪 Logout", use_container_width=True):
             st.session_state.clear()
             st.rerun()

    
    # Main content
    st.markdown("""
        <h1 style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            🎯 Lead Qualifier Pro
        </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Instructions
    with st.expander("📖 How to Use", expanded=False):
        st.markdown("""
            ### Quick Start Guide
            
            1. **Upload CSV File**: Click the file uploader below
            2. **Required Columns**: Your CSV must have these columns:
               - `business_name`: Name of the business
               - `category`: Business category/industry
               - `city`: Business city
               - `state`: Business state
               - `website_url`: Business website URL
               - `email`: Contact email (optional)
            3. **Process**: Click "Process Leads" to start qualification
            4. **Download**: Export your results in Excel, CSV, or JSON format
            
            **💡 Tip**: Each lead costs 1 credit. High-priority leads include personalized outreach messages!
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Single Lead Analyzer Section
    st.header("🎯 Quick Lead Analyzer")
    st.markdown("Analyze a single lead quickly - costs 1 credit")
    
    col1, col2 = st.columns(2)
    
    with col1:
        single_url = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the complete website URL",
            key="single_url"
        )
    
    with col2:
        single_company = st.text_input(
            "Company Name",
            placeholder="Acme Inc.",
            help="Enter the company name",
            key="single_company"
        )
    
    if st.button("🚀 Analyze Single Lead", type="primary", use_container_width=True):
        # Credit check
        if st.session_state.credits <= 0:
            st.error("❌ Insufficient credits! You need at least 1 credit.")
            st.info("💡 Purchase more credits to continue")
        elif not single_url or not single_company:
            st.error("❌ Please provide both website URL and company name")
        else:
            try:
                
                with st.spinner("⚡ Analyzing lead..."):
                    pipeline = LeadQualificationPipeline(OPENAI_API_KEY)
                    
                    # Create lead input
                    lead = LeadInput(
                        business_name=single_company,
                        website_url=single_url,
                        category="Unknown",
                        city="Unknown",
                        state="Unknown",
                        email=""
                    )
                    
                    # Process lead
                    result = pipeline.process_lead(lead)
                    pipeline.cleanup()
                    
                    if result:
                        # Save result
                        st.session_state.results.append(result)
                        save_results(user_email, st.session_state.results)
                        
                        # Deduct credit
                        users = load_users()
                        users[user_email]['credits'] -= 1
                        users[user_email]['total_processed'] += 1
                        save_users(users)
                        st.session_state.credits = users[user_email]['credits']
                        
                        st.success(f"✅ Lead analyzed! Priority: **{result.priority}** | Score: **{result.lead_score}**")
                        st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error analyzing lead: {str(e)}")
                import traceback
                with st.expander("🔍 Technical details"):
                    st.code(traceback.format_exc())
    
    # Display analyzed leads
    if st.session_state.results:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📊 Your Analyzed Leads")
        
        # Quick metrics
        high_count = sum(1 for r in st.session_state.results if r.priority == "HIGH")
        medium_count = sum(1 for r in st.session_state.results if r.priority == "MEDIUM")
        low_count = sum(1 for r in st.session_state.results if r.priority == "LOW")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", len(st.session_state.results))
        col2.metric("🔥 High", high_count)
        col3.metric("📊 Medium", medium_count)
        col4.metric("📉 Low", low_count)
        
        # Results table
        results_df = pd.DataFrame([r.model_dump() for r in st.session_state.results])
        results_df['website_issues'] = results_df['website_issues'].apply(
            lambda x: '; '.join(x) if x else ''
        )
        
        st.dataframe(results_df, use_container_width=True, height=300)
        
        # Show high priority leads with outreach
        high_priority_results = [r for r in st.session_state.results if r.priority == "HIGH"]
        if high_priority_results:
            st.markdown("### 🔥 High Priority Leads - Ready to Contact!")
            for result in high_priority_results:
                with st.expander(f"⭐ {result.business_name} (Score: {result.lead_score})"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**Status:** {result.website_status}")
                        st.markdown(f"**Issues:** {'; '.join(result.website_issues)}")
                    with col2:
                        st.markdown(f"**Score:** {result.lead_score}")
                        st.markdown(f"**Priority:** {result.priority}")
                    
                    st.markdown("**📧 Outreach Message:**")
                    st.info(result.outreach_message)
                    st.code(result.outreach_message, language=None)
        
        # Download results
        st.markdown("### 💾 Download Results")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            excel_data = convert_df_to_excel(results_df)
            st.download_button(
                "📊 Excel",
                excel_data,
                f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                "📄 CSV",
                csv_data,
                f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col3:
            json_data = json.dumps([r.model_dump() for r in st.session_state.results], indent=2)
            st.download_button(
                "📦 JSON",
                json_data,
                f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Batch CSV Upload section
    st.markdown("Upload a CSV file to analyze multiple leads at once")
    
    uploaded_file = st.file_uploader(
        "Upload CSV file with leads",
        type=['csv'],
        help="CSV must contain: business_name, category, city, state, website_url, email"
    )
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            required_cols = ['business_name', 'category', 'city', 'state', 'website_url']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                st.info("💡 Your CSV must have: business_name, category, city, state, website_url, email (optional)")
            else:
                st.success(f"✅ File loaded successfully! Found {len(df)} leads")
                
                # Preview
                st.subheader("📋 Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Process button
                st.markdown("<br>", unsafe_allow_html=True)
                st.header("⚙️ Review & Process")
                
                num_leads = len(df)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Leads to Process", num_leads)
                with col2:
                    st.metric("Credits Required", num_leads)
                
                if num_leads > st.session_state.credits:
                    st.error(f"❌ Insufficient credits! You need {num_leads} credits but only have {st.session_state.credits}")
                    st.info("💡 Purchase more credits to continue")
                else:
                    if st.button("🚀 Process Leads", type="primary", use_container_width=True):
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
    st.dataframe(df_results, use_container_width=True, height=300)
    
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
            use_container_width=True
        )
    
    with col2:
        csv_data = df_results.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"qualified_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        json_data = json.dumps(results_data, indent=2)
        st.download_button(
            label="📦 Download JSON",
            data=json_data,
            file_name=f"qualified_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Success message
    st.markdown("<br>", unsafe_allow_html=True)
    st.success(f"""
    ✅ **Processing Complete!**
    - {num_leads} credits used
    - {users[user_email]['credits']} credits remaining
    - {high_priority} high-priority leads ready to contact
    """)
def is_user_logged_in():
    return bool(st.user.to_dict())

def main():
    init_session_state()

    if not is_user_logged_in():
        login_page()
        st.stop()
    
    # User is logged in, show main app
    main_app()


if __name__ == "__main__":
    main()



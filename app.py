import streamlit as st
import pandas as pd
import json
from io import BytesIO

from src.data.loader import DataLoader
from src.agents.website_inspector import WebsiteInspector
from src.agents.website_classifier import WebsiteClassifier
from src.agents.lead_scorer import LeadScorer
from src.agents.outreach_generator import OutreachGenerator
from src.models.schemas import LeadInput, LeadOutput

# Page config
st.set_page_config(
    page_title="Lead Qualifier Pro",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


class LeadQualificationPipeline:
    """Streamlit-optimized pipeline"""
    
    def __init__(self, api_key: str):
        self.inspector = WebsiteInspector()
        self.classifier = WebsiteClassifier()
        self.scorer = LeadScorer()
        self.outreach_gen = OutreachGenerator(api_key=api_key)
    
    def process_lead(self, lead: LeadInput) -> LeadOutput:
        """Process a single lead"""
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
    """Convert DataFrame to Excel bytes"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Qualified Leads')
    return output.getvalue()


def main():
    # Header
    st.markdown('<p class="main-header">🎯 Lead Qualifier Pro</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Automatically qualify local business leads with AI</p>', unsafe_allow_html=True)
    
    # Sidebar - Settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Get your API key from https://platform.openai.com/api-keys"
        )
        
        st.markdown("---")
        
        st.subheader("📊 Scoring Rules")
        st.info("""
        **HIGH Priority (Score ≥ 10):**
        - No website or weak website
        - Local service business
        - Free email (Gmail/Yahoo)
        
        **MEDIUM Priority (Score 6-9):**
        - Weak website
        
        **LOW Priority (Score ≤ 5):**
        - Acceptable website
        """)
        
        st.markdown("---")
        
        st.subheader("📋 Required CSV Format")
        st.code("""business_name,category,city,state,website_url,email
Joe's Plumbing,Plumbing,Austin,TX,,joe@gmail.com""", language="csv")
        
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
            mime="text/csv"
        )
    
    # Main content
    if not api_key:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to get started")
        st.info("""
        **Don't have an API key?**
        1. Go to https://platform.openai.com/api-keys
        2. Sign up or log in
        3. Create a new API key
        4. Paste it in the sidebar
        """)
        return
    
    # File upload
    st.header("1️⃣ Upload Your Leads")
    uploaded_file = st.file_uploader(
        "Choose a CSV file with your business leads",
        type=['csv'],
        help="Upload a CSV file with columns: business_name, category, city, state, website_url, email"
    )
    
    if uploaded_file is not None:
        # Preview uploaded data
        try:
            df_preview = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)
            
            st.success(f"✅ Loaded {len(df_preview)} leads")
            
            with st.expander("👀 Preview uploaded data"):
                st.dataframe(df_preview.head(10))
            
            # Process button
            st.header("2️⃣ Process Leads")
            
            col1, col2, col3 = st.columns(3)
            with col2:
                process_button = st.button("🚀 Start Processing", type="primary", use_container_width=True)
            
            if process_button:
                try:
                    # Initialize pipeline
                    with st.spinner("Initializing AI agents..."):
                        pipeline = LeadQualificationPipeline(api_key=api_key)
                    
                    # Load data
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
                        st.error("❌ No valid leads found in CSV")
                        return
                    
                    # Process leads with progress bar
                    st.header("3️⃣ Processing...")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = []
                    total = len(leads)
                    
                    for idx, lead in enumerate(leads):
                        status_text.text(f"Processing {idx + 1}/{total}: {lead.business_name}")
                        
                        try:
                            result = pipeline.process_lead(lead)
                            results.append(result)
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
                    
                    status_text.text("✅ Processing complete!")
                    pipeline.cleanup()
                    
                    # Results summary
                    st.header("4️⃣ Results")
                    
                    high_priority = sum(1 for r in results if r.priority == 'HIGH')
                    medium_priority = sum(1 for r in results if r.priority == 'MEDIUM')
                    low_priority = sum(1 for r in results if r.priority == 'LOW')
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Leads", len(results))
                    with col2:
                        st.metric("🔥 HIGH Priority", high_priority)
                    with col3:
                        st.metric("📊 MEDIUM Priority", medium_priority)
                    with col4:
                        st.metric("📉 LOW Priority", low_priority)
                    
                    # Convert to DataFrame
                    results_data = [r.model_dump() for r in results]
                    df_results = pd.DataFrame(results_data)
                    df_results['website_issues'] = df_results['website_issues'].apply(
                        lambda x: '; '.join(x) if x else ''
                    )
                    
                    # Show results
                    st.subheader("📋 All Results")
                    st.dataframe(df_results, use_container_width=True)
                    
                    # High priority leads
                    if high_priority > 0:
                        st.subheader("🔥 HIGH Priority Leads - Ready to Contact")
                        high_df = df_results[df_results['priority'] == 'HIGH']
                        
                        for idx, row in high_df.iterrows():
                            with st.expander(f"⭐ {row['business_name']} (Score: {row['lead_score']})"):
                                st.write(f"**Status:** {row['website_status']}")
                                st.write(f"**Issues:** {row['website_issues']}")
                                st.write("**Outreach Message:**")
                                st.info(row['outreach_message'])
                    
                    # Download options
                    st.header("5️⃣ Download Results")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Excel download
                        excel_data = convert_df_to_excel(df_results)
                        st.download_button(
                            label="📊 Download Excel",
                            data=excel_data,
                            file_name="qualified_leads.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    with col2:
                        # CSV download
                        csv_data = df_results.to_csv(index=False)
                        st.download_button(
                            label="📄 Download CSV",
                            data=csv_data,
                            file_name="qualified_leads.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    # JSON download (optional)
                    with st.expander("Advanced: Download as JSON"):
                        json_data = json.dumps(results_data, indent=2)
                        st.download_button(
                            label="📦 Download JSON",
                            data=json_data,
                            file_name="qualified_leads.json",
                            mime="application/json"
                        )
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Show error details"):
                        st.code(traceback.format_exc())
        
        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Lead Qualifier Pro v1.0 | Built with Streamlit & OpenAI</p>
        <p>💡 Need help? Check the sidebar for instructions</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
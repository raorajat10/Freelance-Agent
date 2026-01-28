import streamlit as st
import pandas as pd
import json
from io import BytesIO
import os
from datetime import datetime
import hashlib
import time

from src.agents.website_inspector import WebsiteInspector
from src.agents.website_classifier import WebsiteClassifier
from src.agents.lead_scorer import LeadScorer
from src.agents.outreach_generator import OutreachGenerator
from src.models.schemas import LeadInput, LeadOutput

# Page config
st.set_page_config(
    page_title="Lead Qualifier Pro - AI Lead Qualification",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Payment Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")  # For India: Razorpay
STRIPE_KEY = os.getenv("STRIPE_KEY", "")  # For International: Stripe

USER_DB_FILE = "users.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'credits' not in st.session_state:
        st.session_state.credits = 0
    if 'show_payment' not in st.session_state:
        st.session_state.show_payment = False
    if 'processing' not in st.session_state:
        st.session_state.processing = False

# Advanced CSS with animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        animation: slideDown 0.8s ease-out;
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
        font-size: 1.3rem;
        animation: fadeIn 1s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .pricing-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 1.5rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .pricing-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.6);
    }
    
    .pricing-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        transform: rotate(45deg);
        transition: all 0.6s ease;
    }
    
    .pricing-card:hover::before {
        top: -30%;
        left: -30%;
    }
    
    .popular-badge {
        position: absolute;
        top: 20px;
        right: 20px;
        background: #ffd700;
        color: #000;
        padding: 0.3rem 0.8rem;
        border-radius: 2rem;
        font-weight: bold;
        font-size: 0.8rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .feature-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
        color: black;
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .feature-box:hover {
        transform: translateX(10px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .credit-badge {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 3rem;
        font-weight: bold;
        display: inline-block;
        font-size: 1.2rem;
        box-shadow: 0 5px 15px rgba(46, 204, 113, 0.4);
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .payment-modal {
        background: white;
        padding: 2rem;
        border-radius: 1.5rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        margin: 2rem 0;
        border: 2px solid #667eea;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        font-weight: 600;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    
    .success-animation {
        animation: successPop 0.6s ease-out;
    }
    
    @keyframes successPop {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .progress-bar-custom {
        height: 30px;
        border-radius: 15px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s ease;
    }
    
    .testimonial {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        color: black;
        font-style: italic;
    }
    
    .upi-button {
        background: linear-gradient(135deg, #00C853 0%, #00E676 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 0.8rem;
        font-weight: bold;
        text-align: center;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(0, 200, 83, 0.4);
    }
    
    .upi-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 200, 83, 0.6);
    }
</style>
""", unsafe_allow_html=True)


class LeadQualificationPipeline:
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
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Qualified Leads')
    return output.getvalue()


def show_payment_modal(package_name, credits, price):
    """Interactive payment modal"""
    st.markdown(f"""
    <div class="payment-modal">
        <h2 style='text-align: center; color: #667eea;'>💳 Complete Your Purchase</h2>
        <h3 style='text-align: center;'>{package_name}</h3>
        <p style='text-align: center; font-size: 1.2rem;'>{credits} Credits for ₹{price}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Choose Payment Method:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📱 UPI / PhonePe / GPay", use_container_width=True, key="upi"):
            st.session_state.payment_method = "UPI"
            show_upi_payment(price, credits)
    
    with col2:
        if st.button("💳 Credit/Debit Card", use_container_width=True, key="card"):
            st.session_state.payment_method = "Card"
            show_card_payment(price, credits)
    
    with col3:
        if st.button("🏦 Net Banking", use_container_width=True, key="net"):
            st.session_state.payment_method = "NetBanking"
            show_netbanking_payment(price, credits)


def show_upi_payment(price, credits):
    """UPI Payment Interface - Most popular in India"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #00C853 0%, #00E676 100%); 
                padding: 2rem; border-radius: 1rem; color: white; margin: 1rem 0;'>
        <h3>📱 Pay with UPI</h3>
        <p>Use any UPI app: PhonePe, Google Pay, Paytm, BHIM</p>
    </div>
    """, unsafe_allow_html=True)
    
    # UPI ID input
    upi_id = st.text_input("Enter your UPI ID (e.g., yourname@paytm)", key="upi_input")
    
    # OR show QR code
    st.markdown("**OR Scan QR Code:**")
    
    # Generate UPI payment link
    # Format: upi://pay?pa=MERCHANT_UPI&pn=MerchantName&am=AMOUNT&cu=INR
    merchant_upi = "yourmerchant@paytm"  # Replace with your UPI ID
    upi_link = f"upi://pay?pa={merchant_upi}&pn=LeadQualifierPro&am={price}&cu=INR&tn=Credits_{credits}"
    
    # Display QR code (you'd generate this with qrcode library)
    st.info(f"🔗 Payment Link: `{upi_link}`")
    st.code(f"UPI ID: {merchant_upi}\nAmount: ₹{price}\nFor: {credits} credits")
    
    # Transaction ID input
    transaction_id = st.text_input("Enter UPI Transaction ID after payment", key="upi_txn")
    
    if st.button("✅ Verify Payment", type="primary", use_container_width=True):
        if transaction_id:
            # In production: Verify with payment gateway API
            verify_and_add_credits(credits, transaction_id, "UPI")
        else:
            st.error("Please enter transaction ID")


def show_card_payment(price, credits):
    """Card Payment via Razorpay/Stripe"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 1rem; color: white; margin: 1rem 0;'>
        <h3>💳 Pay with Card</h3>
        <p>We accept Visa, Mastercard, Rupay, American Express</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Razorpay Integration (India)
    if RAZORPAY_KEY_ID:
        st.markdown(f"""
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <button id="rzp-button" class="stButton">Pay ₹{price} Now</button>
        <script>
        var options = {{
            "key": "{RAZORPAY_KEY_ID}",
            "amount": {price * 100},
            "currency": "INR",
            "name": "Lead Qualifier Pro",
            "description": "{credits} Credits",
            "handler": function (response) {{
                alert("Payment successful! Transaction ID: " + response.razorpay_payment_id);
                // Send to backend to verify and add credits
            }}
        }};
        var rzp = new Razorpay(options);
        document.getElementById('rzp-button').onclick = function(e) {{
            rzp.open();
            e.preventDefault();
        }}
        </script>
        """, unsafe_allow_html=True)
    else:
        # Manual card input (demo)
        st.text_input("Card Number", placeholder="1234 5678 9012 3456")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Expiry (MM/YY)", placeholder="12/25")
        with col2:
            st.text_input("CVV", placeholder="123", type="password")
        
        if st.button("💳 Pay Now", type="primary", use_container_width=True):
            st.warning("⚠️ Demo mode - Payment gateway not configured. Contact admin.")


def show_netbanking_payment(price, credits):
    """Net Banking Payment"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); 
                padding: 2rem; border-radius: 1rem; color: white; margin: 1rem 0;'>
        <h3>🏦 Pay via Net Banking</h3>
        <p>Select your bank to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    banks = ["SBI", "HDFC", "ICICI", "Axis", "Kotak", "PNB", "Other"]
    selected_bank = st.selectbox("Select Bank", banks)
    
    if st.button(f"Continue with {selected_bank}", type="primary", use_container_width=True):
        st.info(f"Redirecting to {selected_bank} payment gateway...")
        st.warning("⚠️ Demo mode - Payment gateway not configured.")


def verify_and_add_credits(credits, transaction_id, method):
    """Verify payment and add credits"""
    with st.spinner("Verifying payment..."):
        time.sleep(2)  # Simulate verification
        
        # In production: Call payment gateway API to verify
        # For demo: Assume success
        
        users = load_users()
        user_email = st.session_state.user_email
        users[user_email]['credits'] += credits
        users[user_email]['transactions'] = users[user_email].get('transactions', [])
        users[user_email]['transactions'].append({
            'date': datetime.now().isoformat(),
            'credits': credits,
            'method': method,
            'txn_id': transaction_id
        })
        save_users(users)
        st.session_state.credits = users[user_email]['credits']
        
        st.markdown("""
        <div class="success-animation" style='background: #d4edda; padding: 2rem; 
                border-radius: 1rem; text-align: center; margin: 2rem 0;'>
            <h2>🎉 Payment Successful!</h2>
            <p style='font-size: 1.2rem;'>✅ {credits} credits added to your account</p>
        </div>
        """.replace('{credits}', str(credits)), unsafe_allow_html=True)
        
        st.balloons()
        st.session_state.show_payment = False
        time.sleep(2)
        st.rerun()


def login_page():
    """Enhanced login page with social proof"""
    st.markdown('<p class="main-header">🎯 Lead Qualifier Pro</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Lead Qualification for Freelancers & Agencies</p>', unsafe_allow_html=True)
    
    # Social proof
    # col1, col2, col3, col4 = st.columns(4)
    # with col1:
    #     st.markdown("""
    #     <div class="stat-card">
    #         <h2 style='color: #667eea; margin: 0;'>2,500+</h2>
    #         <p style='color: #666; margin: 0;'>Leads Qualified</p>
    #     </div>
    #     """, unsafe_allow_html=True)
    # with col2:
    #     st.markdown("""
    #     <div class="stat-card">
    #         <h2 style='color: #667eea; margin: 0;'>150+</h2>
    #         <p style='color: #666; margin: 0;'>Happy Users</p>
    #     </div>
    #     """, unsafe_allow_html=True)
    # with col3:
    #     st.markdown("""
    #     <div class="stat-card">
    #         <h2 style='color: #667eea; margin: 0;'>4.9/5</h2>
    #         <p style='color: #666; margin: 0;'>Rating</p>
    #     </div>
    #     """, unsafe_allow_html=True)
    # with col4:
    #     st.markdown("""
    #     <div class="stat-card">
    #         <h2 style='color: #667eea; margin: 0;'>24/7</h2>
    #         <p style='color: #666; margin: 0;'>Support</p>
    #     </div>
    #     """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Features
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3 style="color: black;">⚡ Lightning Fast</h3>
            <p>Process 100 leads in under 60 seconds</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3 style="color: black;">🤖 AI-Powered</h3>
            <p>GPT-4 generates personalized outreach</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-box">
            <h3 style="color: black;">💰 Pay Per Use</h3>
            <p>No subscription, buy credits as needed</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Testimonials
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💬 What Users Say")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="testimonial">
            "This tool 10x'd my outreach game. Got 3 new clients in first week!" 
            <br><strong>- Rahul, Freelance Web Developer</strong>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="testimonial">
            "Best ₹500 I've spent. Saves me 5 hours every week!" 
            <br><strong>- Priya, Digital Marketing Agency</strong>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Login/Signup
    tab1, tab2 = st.tabs(["🔐 Login", "✨ Start Free Trial"])
    
    users = load_users()
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if email in users and users[email]['password'] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.credits = users[email]['credits']
                    st.success("✅ Welcome back!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
    
    with tab2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 1rem; color: white; text-align: center; margin-bottom: 2rem;'>
            <h2>🎁 Get 10 FREE Credits</h2>
            <p style='font-size: 1.2rem;'>No credit card required • Start in 30 seconds</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            agree = st.checkbox("I agree to Terms & Conditions")
            submit = st.form_submit_button("🚀 Start Free Trial", use_container_width=True)
            
            if submit:
                if not agree:
                    st.error("Please accept terms")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                elif new_email in users:
                    st.error("Email already registered")
                else:
                    users[new_email] = {
                        'password': hash_password(new_password),
                        'credits': 10,
                        'total_processed': 0,
                        'created_at': datetime.now().isoformat(),
                        'transactions': []
                    }
                    save_users(users)
                    st.session_state.logged_in = True
                    st.session_state.user_email = new_email
                    st.session_state.credits = 10
                    st.balloons()
                    st.success("🎉 Account created! You have 10 free credits!")
                    time.sleep(2)
                    st.rerun()
    
    # Pricing
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("💳 Simple Pricing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="pricing-card" style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);">
            <h3>Starter</h3>
            <h1>$25</h1>
            <p style='font-size: 1.2rem;'>25 Credits</p>
            <p>$1 per lead</p>
            <p style='font-size: 0.9em; margin-top: 1rem;'>✓ AI Outreach Messages<br>✓ Excel/CSV Export<br>✓ Email Support</p>
        </div>
        """, unsafe_allow_html=True)
    
    # with col2:
    #     st.markdown("""
    #     <div class="pricing-card">
    #         <div class="popular-badge">⭐ MOST POPULAR</div>
    #         <h3>Professional</h3>
    #         <h1>$70</h1><p style='font-size: 1.2rem;'>(30% off)</p>
    #         <p style='font-size: 1.2rem;'>100 Credits</p>
    #         <p>$1 per lead</p>
    #         <p style='font-size: 0.9em; margin-top: 1rem;'>✓ Everything in Starter<br>✓ Priority Support<br>✓ Bulk Processing</p>
    #     </div>
    #     """, unsafe_allow_html=True)
    
    # with col3:
    #     st.markdown("""
    #     <div class="pricing-card" style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);">
    #         <h3>Agency</h3>
    #         <h1>$250</h1><p style='font-size: 1.2rem;'>(50% off)</p>
    #         <p style='font-size: 1.2rem;'>500 Credits</p>
    #         <p>$1 per lead</p>
    #         <p style='font-size: 0.9em; margin-top: 1rem;'>✓ Everything in Pro<br>✓ API Access<br>✓ WhatsApp Support</p>
    #     </div>
    #     """, unsafe_allow_html=True)


def main_app():
    """Main app with payment integration"""
    users = load_users()
    user_email = st.session_state.user_email
    user_data = users[user_email]
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown('<p class="main-header" style="text-align: left; font-size: 2.5rem;">🎯 Lead Qualifier Pro</p>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="credit-badge">💳 {user_data["credits"]} Credits</div>', unsafe_allow_html=True)
    with col3:
        if st.button("➕ Buy Credits", use_container_width=True):
            st.session_state.show_payment = True
    
    # Payment Modal
    # if st.session_state.show_payment:
    #     st.markdown("---")
    #     col1, col2, col3 = st.columns(3)
        
    #     with col1:
    #         if st.button("📦 Starter Pack\n₹500 for 50 credits", use_container_width=True, key="buy1"):
    #             show_payment_modal("Starter Pack", 50, 500)
        
    #     with col2:
    #         if st.button("⭐ Pro Pack\n₹1,499 for 200 credits", use_container_width=True, key="buy2"):
    #             show_payment_modal("Pro Pack", 200, 1499)
        
    #     with col3:
    #         if st.button("🚀 Agency Pack\n₹2,999 for 500 credits", use_container_width=True, key="buy3"):
    #             show_payment_modal("Agency Pack", 500, 2999)
        
    #     if st.button("❌ Close", key="close_payment"):
    #         st.session_state.show_payment = False
    #         st.rerun()
        
    #     st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user_email}")
        st.metric("Credits", user_data['credits'])
        st.metric("Total Processed", user_data['total_processed'])
        
        st.markdown("---")
        
        # Transaction history
        if 'transactions' in user_data and user_data['transactions']:
            with st.expander("💰 Purchase History"):
                for txn in user_data['transactions'][-5:]:  # Last 5 transactions
                    st.text(f"{txn['date'][:10]}: +{txn['credits']} credits ({txn['method']})")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.credits = 0
            st.rerun()
        
        st.markdown("---")
        
        # Quick guide
        st.info("""
        **Quick Guide:**
        1. Upload CSV file
        2. Review cost
        3. Click Process
        4. Download results
        """)
        
        st.markdown("---")
        
        # Sample CSV download
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
            "📥 Download Sample CSV",
            csv,
            "sample_leads.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Support info
        st.markdown("""
        **Need Help?**
        📧 support@leadqualifier.com
        💬 Chat: +91-XXXXXXXXXX
        """)
    
    # Main content area
    if not OPENAI_API_KEY:
        st.error("⚠️ Service temporarily unavailable. Contact support.")
        return
    
    # Upload section
    st.header("1️⃣ Upload Your Leads")
    uploaded_file = st.file_uploader(
        "Drop your CSV file here or click to browse",
        type=['csv'],
        help="CSV must have: business_name, category, city, state, website_url, email"
    )
    
    if uploaded_file is not None:
        try:
            df_preview = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)
            num_leads = len(df_preview)
            
            st.success(f"✅ Loaded {num_leads} leads successfully!")
            
            with st.expander("👀 Preview uploaded data (first 10 rows)"):
                st.dataframe(df_preview.head(10), use_container_width=True)
            
            # Cost calculation
            st.header("2️⃣ Review & Process")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Leads to Process", num_leads)
            with col2:
                st.metric("💳 Credits Required", num_leads)
            with col3:
                remaining = user_data['credits'] - num_leads
                st.metric("💰 Credits After", remaining, delta=f"-{num_leads}")
            
            # Check if user has enough credits
            if user_data['credits'] < num_leads:
                shortage = num_leads - user_data['credits']
                st.error(f"❌ Insufficient credits! You need {shortage} more credits.")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("💳 Buy 50 Credits (₹500)", use_container_width=True):
                        st.session_state.show_payment = True
                        st.rerun()
                with col2:
                    if st.button("⭐ Buy 200 Credits (₹1,499)", use_container_width=True):
                        st.session_state.show_payment = True
                        st.rerun()
                with col3:
                    if st.button("🚀 Buy 500 Credits (₹2,999)", use_container_width=True):
                        st.session_state.show_payment = True
                        st.rerun()
                
                return
            
            # Process button
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                process_button = st.button(
                    f"🚀 Process {num_leads} Leads ({num_leads} Credits)",
                    type="primary",
                    use_container_width=True
                )
            
            if process_button:
                try:
                    # Initialize pipeline
                    with st.spinner("🤖 Initializing AI agents..."):
                        pipeline = LeadQualificationPipeline(api_key=OPENAI_API_KEY)
                    
                    # Load and validate leads
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
                    
                    # Process leads with animated progress
                    st.header("3️⃣ Processing...")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    result_preview = st.empty()
                    
                    results = []
                    total = len(leads)
                    
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
                            
                            # Show live preview of high-priority leads
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
                    <div class="success-animation" style='background: #d4edda; 
                                color: #155724; padding: 1.5rem; border-radius: 0.5rem; 
                                text-align: center; font-size: 1.2rem; font-weight: bold;'>
                        ✅ Processing Complete!
                    </div>
                    """, unsafe_allow_html=True)
                    
                    pipeline.cleanup()
                    
                    # Deduct credits and update user data
                    users[user_email]['credits'] -= num_leads
                    users[user_email]['total_processed'] += num_leads
                    save_users(users)
                    st.session_state.credits = users[user_email]['credits']
                    
                    # Display results
                    st.header("4️⃣ Results & Insights")
                    
                    high_priority = sum(1 for r in results if r.priority == 'HIGH')
                    medium_priority = sum(1 for r in results if r.priority == 'MEDIUM')
                    low_priority = sum(1 for r in results if r.priority == 'LOW')
                    
                    # Metrics with custom styling
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown("""
                        <div class="stat-card" style='border-left: 4px solid #667eea;'>
                            <h2 style='color: #667eea; margin: 0;'>{}</h2>
                            <p style='color: #666; margin: 0;'>Total Leads</p>
                        </div>
                        """.format(len(results)), unsafe_allow_html=True)
                    with col2:
                        st.markdown("""
                        <div class="stat-card" style='border-left: 4px solid #e74c3c;'>
                            <h2 style='color: #e74c3c; margin: 0;'>🔥 {}</h2>
                            <p style='color: #666; margin: 0;'>HIGH Priority</p>
                        </div>
                        """.format(high_priority), unsafe_allow_html=True)
                    with col3:
                        st.markdown("""
                        <div class="stat-card" style='border-left: 4px solid #f39c12;'>
                            <h2 style='color: #f39c12; margin: 0;'>📊 {}</h2>
                            <p style='color: #666; margin: 0;'>MEDIUM Priority</p>
                        </div>
                        """.format(medium_priority), unsafe_allow_html=True)
                    with col4:
                        st.markdown("""
                        <div class="stat-card" style='border-left: 4px solid #95a5a6;'>
                            <h2 style='color: #95a5a6; margin: 0;'>📉 {}</h2>
                            <p style='color: #666; margin: 0;'>LOW Priority</p>
                        </div>
                        """.format(low_priority), unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Convert to DataFrame
                    results_data = [r.model_dump() for r in results]
                    df_results = pd.DataFrame(results_data)
                    df_results['website_issues'] = df_results['website_issues'].apply(
                        lambda x: '; '.join(x) if x else ''
                    )
                    
                    # Show full results table
                    st.subheader("📋 All Results")
                    st.dataframe(df_results, use_container_width=True, height=300)
                    
                    # High-priority leads with outreach messages
                    if high_priority > 0:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.subheader("🔥 HIGH Priority Leads - Ready to Contact!")
                        
                        high_df = df_results[df_results['priority'] == 'HIGH']
                        
                        for idx, row in high_df.iterrows():
                            with st.expander(
                                f"⭐ {row['business_name']} (Score: {row['lead_score']}) - {row['website_status']}",
                                expanded=(idx == high_df.index[0])  # Expand first one
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
                                
                                # Copy button
                                st.code(row['outreach_message'], language=None)
                    
                    # Download section
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.header("5️⃣ Download Your Results")
                    
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
                    
                    st.balloons()
                
                except Exception as e:
                    st.error(f"❌ Processing Error: {str(e)}")
                    import traceback
                    with st.expander("🔍 Show technical details"):
                        st.code(traceback.format_exc())
        
        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")
            st.info("💡 Make sure your CSV has the required columns: business_name, category, city, state, website_url, email")


def main():
    """Main entry point"""
    init_session_state()
    
    if st.session_state.logged_in:
        main_app()
    else:
        login_page()


if __name__ == "__main__":
    main()    
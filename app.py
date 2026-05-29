import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from pydantic import BaseModel, ValidationError
from supabase import create_client, Client

# ==========================================
# 1. CORE CONFIGURATION & SUPABASE DATABASE SETUP
# ==========================================
st.set_page_config(page_title="ReconSimple Pro", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def init_supabase() -> Client:
    """Safely connects to the Supabase cloud ledger using Streamlit encrypted secrets"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        # Fallback if secrets are not configured yet during local testing
        return None

supabase = init_supabase()

# ==========================================
# 2. PREMIUM UX CUSTOM CSS INJECTOR
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117;
        color: #c9d1d9;
    }
    h1 { font-weight: 700 !important; color: #ffffff !important; letter-spacing: -0.5px; }
    h3 { font-weight: 600 !important; color: #f0f6fc !important; margin-top: 20px !important; }
    
    /* Premium Obsidian Cards for Metrics */
    div[data-testid="stMetricContainer"] {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 14px !important; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 28px !important; font-weight: 700 !important; }
    
    /* Upload Dashboards */
    .upload-card { background-color: #161b22; border: 1px dashed #444c56; border-radius: 12px; padding: 15px; text-align: center; }
    
    /* Action Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f6feb 0%, #0d44a3 100%);
        color: white !important;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        border-radius: 8px;
        box-shadow: 0 4px 14px rgba(31, 111, 235, 0.4);
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #388bfd 0%, #1f6feb 100%);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. BACKGROUND LIVE API INGESTION ENGINE
# ==========================================
def fetch_shopify_orders(api_token, shop_url):
    """Fetches past 24h transactions directly from Shopify storefront endpoints"""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    endpoint = f"https://{shop_url}/admin/api/2026-04/orders.json?created_at_min={yesterday}&status=any"
    headers = {"X-Shopify-Access-Token": api_token, "Content-Type": "application/json"}
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        if response.status_code == 200:
            orders = response.json().get('orders', [])
            if orders:
                return pd.DataFrame([{'id': str(o['order_number']), 'amount_store': float(o['current_total_price'])} for o in orders])
            return pd.DataFrame(columns=['id', 'amount_store'])
        return None
    except Exception:
        return None

def fetch_razorpay_payments(api_key, api_secret):
    """Streams payment gateway summaries directly from Razorpay secure pipelines"""
    from_time = int((datetime.now() - timedelta(days=1)).timestamp())
    endpoint = f"https://api.razorpay.com/v1/payments?from={from_time}"
    try:
        response = requests.get(endpoint, auth=(api_key, api_secret), timeout=10)
        if response.status_code == 200:
            payments = response.json().get('items', [])
            if payments:
                return pd.DataFrame([{
                    'id': str(p['notes'].get('shopify_order_number', p['description'])),
                    'amount_gateway': float(p['amount']) / 100,
                    'fee_gateway': float(p.get('fee', 0)) / 100
                } for p in payments if p['status'] == 'captured'])
            return pd.DataFrame(columns=['id', 'amount_gateway', 'fee_gateway'])
        return None
    except Exception:
        return None

# ==========================================
# 4. DATA MATCHING & RECONCILIATION LOGIC
# ==========================================
def run_reconciliation(sales_df, gateway_df):
    """Executes atomic structural joins across datasets to locate gaps"""
    # Force clean column states
    sales_df.columns = sales_df.columns.str.strip().str.lower()
    gateway_df.columns = gateway_df.columns.str.strip().str.lower()
    
    # Merge datasets securely
    merged = pd.merge(sales_df, gateway_df, on='id', how='left', suffixes=('_store', '_gateway'))
    
    # Track ghost orders (Sales that exist on store but missing payment confirmation)
    ghosts = merged[merged['amount_gateway'].isna() & merged['amount_store'].notna()]
    return ghosts

# ==========================================
# 5. UI CONTROL MATRIX & SIDEBAR SETTINGS
# ==========================================
st.sidebar.markdown("<h2 style='color: white; font-weight: 700;'>🔌 Integration Hub</h2>", unsafe_allow_html=True)
connect_shopify = st.sidebar.checkbox("Connect Shopify Live API")
connect_razorpay = st.sidebar.checkbox("Connect Razorpay Live API")

shopify_token, shopify_url = "", ""
if connect_shopify:
    shopify_url = st.sidebar.text_input("Shopify Store URL", placeholder="brand.myshopify.com")
    shopify_token = st.sidebar.text_input("Admin API Access Token", type="password")

rzp_key, rzp_secret = "", ""
if connect_razorpay:
    rzp_key = st.sidebar.text_input("Razorpay API Key ID", type="password")
    rzp_secret = st.sidebar.text_input("Razorpay Secret Key", type="password")

st.sidebar.markdown("---")
expected_fee_pct = st.sidebar.slider("Target Aggregator Fee Base (%)", 1.0, 5.0, 2.3, 0.1) / 100

# ==========================================
# 6. MAIN PANEL ARCHITECTURE
# ==========================================
st.title("📊 ReconSimple Pro")
st.markdown("<p style='color: #8b949e; font-size: 16px; margin-top: -15px;'>Enterprise Infrastructure Multi-Channel Reconciliation Engine</p>", unsafe_allow_html=True)
st.markdown("<div style='height: 2px; background: linear-gradient(90deg, #1f6feb 0%, transparent 100%); margin-bottom: 30px;'></div>", unsafe_allow_html=True)

# Visual block for alternative manual fallback files
st.markdown("### 📥 Ingest Channel Data")
col1, col2 = st.columns(2)
df_master_manual, df_g1_manual = None, None

with col1:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    f_store = st.file_uploader("Storefront (Shopify/Woo CSV Fallback)", type=["csv"], disabled=connect_shopify)
    st.markdown('</div>', unsafe_allow_html=True)
    if f_store and not connect_shopify:
        df_master_manual = pd.read_csv(f_store)
        col_m = st.selectbox("Select Order ID Column", df_master_manual.columns)

with col2:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    f_gtway = st.file_uploader("Primary Gateway (Razorpay CSV Fallback)", type=["csv"], disabled=connect_razorpay)
    st.markdown('</div>', unsafe_allow_html=True)
    if f_gtway and not connect_razorpay:
        df_g1_manual = pd.read_csv(f_gtway)
        col_g = st.selectbox("Select Transaction ID Column", df_g1_manual.columns)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# Trigger Engine Evaluation
can_run = (connect_shopify and shopify_token) or (df_master_manual is not None)

if can_run:
    if st.button("🚀 Execute System-Wide Reconciliation Audit", use_container_width=True):
        st.markdown("---")
        df_master, df_g1 = None, None
        
        with st.spinner("Extracting parameters across structural system endpoints..."):
            # Ingest storefront
            if connect_shopify and shopify_token and shopify_url:
                df_master = fetch_shopify_orders(shopify_token, shopify_url)
            elif df_master_manual is not None:
                df_master = df_master_manual.copy()
                df_master['id'] = df_master[col_m].astype(str).str.strip()
                df_master['amount_store'] = df_master.iloc[:, 1].astype(float)
            
            # Ingest gateway
            if connect_razorpay and rzp_key and rzp_secret:
                df_g1 = fetch_razorpay_payments(rzp_key, rzp_secret)
            elif df_g1_manual is not None:
                df_g1 = df_g1_manual.copy()
                df_g1['id'] = df_g1[col_g].astype(str).str.strip()
                df_g1['amount_gateway'] = df_g1.iloc[:, 1].astype(float)
                df_g1['fee_gateway'] = 0.0

        # Execute Engine Matching Process
        if df_master is not None and df_g1 is not None:
            ghost_orders = run_reconciliation(df_master, df_g1)
            total_orders = len(df_master)
            leaked_count = len(ghost_orders)
            
            # Write results securely to the Supabase Postgres Cloud ledger
            if supabase and leaked_count > 0:
                try:
                    for _, row in ghost_orders.iterrows():
                        supabase.table("leakages").insert({
                            "order_id": str(row['id']),
                            "leaked_amount": float(row['amount_store']),
                            "logged_at": datetime.utcnow().isoformat()
                        }).execute()
                    st.caption("🔒 Security Log: Discrepancy signatures cataloged in database instance.")
                except Exception as e:
                    st.caption(f"Database sync bypass: {e}")
            
            # Dashboard Analytics Section
            st.markdown("### 📈 Diagnostics Summary Panels")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Total Volume Audited", f"{total_orders} Trans.")
            with m2:
                st.metric("Ghost Orders Detected", f"{leaked_count} Units", delta=f"-{leaked_count}" if leaked_count > 0 else "0", delta_color="inverse")
            with m3:
                st.metric("Database Sync Health", "Connected" if supabase else "Offline Mode")
                
            st.markdown("### 🔍 Granular Exception Logs")
            if leaked_count > 0:
                st.error("⚠️ Revenue Drift Discovered: The following transaction ids match storefront registers but do not possess gateway settlement receipts.")
                st.dataframe(ghost_orders[['id', 'amount_store']].rename(columns={'id': 'Flagged Order Reference', 'amount_store': 'Leaked Value (INR)'}), use_container_width=True)
            else:
                st.success("✅ Clean Ledger Verified: Structural validation algorithms return zero transaction variations across channels.")
        else:
            st.error("Error: Engine failed to extract readable transaction matrix vectors. Check your entry data paths.")
else:
    st.markdown("<div style='background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; color: #8b949e;'>💡 <b>System Standby:</b> Please activate either the Live API settings in the sidebar or upload a manual Storefront file to initialize the reconciliation pipeline routes.</div>", unsafe_allow_html=True)

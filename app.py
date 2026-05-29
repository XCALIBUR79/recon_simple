import streamlit as st
import pandas as pd
import requests
import boto3  # For Amazon Selling Partner API integration
from datetime import datetime, timedelta
from supabase import create_client, Client

# ==========================================
# 1. INITIALIZATION & DATABASE HUB SETUP
# ==========================================
st.set_page_config(page_title="ReconSimple Pro", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# Modern Dark UI Aesthetics
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
    div[data-testid="stMetricContainer"] {
        background: rgba(22, 27, 34, 0.8); border: 1px solid #30363d; border-radius: 12px; padding: 20px 24px;
    }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 14px !important; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 28px !important; font-weight: 700 !important; }
    .upload-card { background-color: #161b22; border: 1px dashed #444c56; border-radius: 12px; padding: 15px; text-align: center; }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f6feb 0%, #0d44a3 100%); color: white !important;
        border: none; padding: 12px 24px; font-weight: 600; border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MULTI-CHANNEL AUTOMATED API PIPELINES
# ==========================================
def fetch_shopify_orders(api_token, shop_url):
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    endpoint = f"https://{shop_url}/admin/api/2026-04/orders.json?created_at_min={yesterday}&status=any"
    headers = {"X-Shopify-Access-Token": api_token, "Content-Type": "application/json"}
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        if response.status_code == 200:
            orders = response.json().get('orders', [])
            return pd.DataFrame([{'id': str(o['order_number']), 'amount_store': float(o['current_total_price'])} for o in orders])
        return None
    except Exception: return None

def fetch_razorpay_payments(api_key, api_secret):
    from_time = int((datetime.now() - timedelta(days=1)).timestamp())
    endpoint = f"https://api.razorpay.com/v1/payments?from={from_time}"
    try:
        response = requests.get(endpoint, auth=(api_key, api_secret), timeout=10)
        if response.status_code == 200:
            payments = response.json().get('items', [])
            return pd.DataFrame([{'id': str(p['notes'].get('shopify_order_number', p['description'])), 'amount_rzp': float(p['amount']) / 100, 'fee_rzp': float(p.get('fee', 0)) / 100} for p in payments if p['status'] == 'captured'])
        return None
    except Exception: return None

def fetch_stripe_charges(api_key):
    """NEW API: Connects to Stripe Core Ledger API"""
    endpoint = "https://api.stripe.com/v1/charges?limit=100"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        if response.status_code == 200:
            charges = response.json().get('data', [])
            return pd.DataFrame([{'id': str(c['metadata'].get('order_id', c['id'])), 'amount_stripe': float(c['amount']) / 100} for c in charges if c['paid'] == True])
        return None
    except Exception: return None

def fetch_amazon_orders(aws_access_key, aws_secret_key, marketplace_id):
    """NEW API: Connects to Amazon Selling Partner (SP) API using Boto3"""
    try:
        client = boto3.client('orders', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name='us-east-1')
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        response = client.list_orders(MarketplaceIds=[marketplace_id], CreatedAfter=yesterday)
        orders = response.get('Orders', [])
        return pd.DataFrame([{'id': str(o['AmazonOrderId']), 'amount_amazon': float(o['OrderTotal']['Amount'])} for o in orders])
    except Exception:
        return pd.DataFrame(columns=['id', 'amount_amazon'])

# ==========================================
# 3. SIDEBAR CREDENTIAL VAULT (INTEGRATION HUB)
# ==========================================
st.sidebar.markdown("<h2 style='color: white; font-weight: 700;'>🔌 Integration Hub</h2>", unsafe_allow_html=True)

# Spoke toggles
connect_shopify = st.sidebar.checkbox("1. Connect Shopify (Master Hub)")
connect_razorpay = st.sidebar.checkbox("2. Connect Razorpay Spoke")
connect_stripe = st.sidebar.checkbox("3. Connect Stripe Spoke")
connect_amazon = st.sidebar.checkbox("4. Connect Amazon Spoke")

# Dynamic inputs based on selection
shopify_token, shopify_url = "", ""
if connect_shopify:
    shopify_url = st.sidebar.text_input("Shopify Store URL", placeholder="brand.myshopify.com")
    shopify_token = st.sidebar.text_input("Shopify API Access Token", type="password")

rzp_key, rzp_secret = "", ""
if connect_razorpay:
    rzp_key = st.sidebar.text_input("Razorpay Key ID", type="password")
    rzp_secret = st.sidebar.text_input("Razorpay Secret Key", type="password")

stripe_key = ""
if connect_stripe:
    stripe_key = st.sidebar.text_input("Stripe Secret API Key", type="password")

amzn_key, amzn_secret, amzn_id = "", "", ""
if connect_amazon:
    amzn_key = st.sidebar.text_input("AWS Access Key ID", type="password")
    amzn_secret = st.sidebar.text_input("AWS Secret Key", type="password")
    amzn_id = st.sidebar.text_input("Amazon Marketplace ID")

# ==========================================
# 4. MAIN INTERFACE: HUB DESIGN
# ==========================================
st.title("📊 ReconSimple Pro")
st.markdown("<p style='color: #8b949e; font-size: 16px; margin-top: -15px;'>Hub-and-Spoke Enterprise Multi-Channel Reconciliation Engine</p>", unsafe_allow_html=True)
st.markdown("<div style='height: 2px; background: linear-gradient(90deg, #1f6feb 0%, transparent 100%); margin-bottom: 30px;'></div>", unsafe_allow_html=True)

st.markdown("### 📥 Ingest Channel Records")
df_master = None

# Enforcing your design rule: The Master File Box must be populated first
if not connect_shopify:
    st.markdown('<div class="upload-card" style="border-color: #58a6ff;">', unsafe_allow_html=True)
    f_store = st.file_uploader("👑 UPLOAD MASTER FILE (Shopify/WooCommerce Sales Orders CSV Summary)", type=["csv"])
    st.markdown('</div>', unsafe_allow_html=True)
    if f_store:
        df_master_raw = pd.read_csv(f_store)
        col_m = st.selectbox("Identify Unique Order ID Field from Master File", df_master_raw.columns)
        df_master = df_master_raw.copy()
        df_master['id'] = df_master[col_m].astype(str).str.strip()
        df_master['amount_store'] = df_master.iloc[:, 1].astype(float)
else:
    st.info("⚡ Shopify activated as Master API Hub. Bypassing manual Master Upload container.")

# Operational Execution Trigger
ready_to_audit = (connect_shopify and shopify_token) or (df_master is not None)

if ready_to_audit:
    if st.button("🚀 Execute System-Wide Cross-Channel Audit", use_container_width=True):
        st.markdown("---")
        
        with st.spinner("Streaming transaction logs across connected API Spoke paths..."):
            # If Master is API base instead of CSV upload
            if connect_shopify:
                df_master = fetch_shopify_orders(shopify_token, shopify_url)
            
            # If Master fails to extract data, stop process
            if df_master is None or df_master.empty:
                st.error("Audit Terminated: Master transaction tracking hub contains empty vectors.")
                st.stop()

            # Prepare baseline reporting parameters
            leaks_detected = 0
            
            # Start Tabular Analysis Report UI
            tab_names = []
            if connect_razorpay: tab_names.append("Razorpay Status")
            if connect_stripe: tab_names.append("Stripe Status")
            if connect_amazon: tab_names.append("Amazon Status")
            if not tab_names: tab_names = ["System Overview"]
            
            ui_tabs = st.tabs(tab_names)
            tab_idx = 0

            # --------------------------------------------------
            # SPOKE 1: RAZORPAY CROSS-EXAMINATION
            # --------------------------------------------------
            if connect_razorpay:
                with ui_tabs[tab_idx]:
                    df_rzp = fetch_razorpay_payments(rzp_key, rzp_secret)
                    if df_rzp is not None:
                        m_rzp = pd.merge(df_master, df_rzp, on='id', how='left')
                        ghosts = m_rzp[m_rzp['amount_rzp'].isna()]
                        if not ghosts.empty:
                            st.error(f"⚠️ Flagged {len(ghosts)} transactions missing from Razorpay ledger records.")
                            st.dataframe(ghosts[['id', 'amount_store']], use_container_width=True)
                            leaks_detected += len(ghosts)
                        else: st.success("✅ Razorpay channel matches the Master File perfectly.")
                    else: st.warning("Razorpay API query returned no records for this cycle.")
                tab_idx += 1

            # --------------------------------------------------
            # SPOKE 2: STRIPE CROSS-EXAMINATION
            # --------------------------------------------------
            if connect_stripe:
                with ui_tabs[tab_idx]:
                    df_stripe = fetch_stripe_charges(stripe_key)
                    if df_stripe is not None:
                        m_stripe = pd.merge(df_master, df_stripe, on='id', how='left')
                        ghosts_strp = m_stripe[m_stripe['amount_stripe'].isna()]
                        if not ghosts_strp.empty:
                            st.error(f"⚠️ Flagged {len(ghosts_strp)} transactions missing from Stripe ledger records.")
                            st.dataframe(ghosts_strp[['id', 'amount_store']], use_container_width=True)
                            leaks_detected += len(ghosts_strp)
                        else: st.success("✅ Stripe channel matches the Master File perfectly.")
                    else: st.warning("Stripe API query returned no records for this cycle.")
                tab_idx += 1

            # --------------------------------------------------
            # SPOKE 3: AMAZON CROSS-EXAMINATION
            # --------------------------------------------------
            if connect_amazon:
                with ui_tabs[tab_idx]:
                    df_amzn = fetch_amazon_orders(amzn_key, amzn_secret, amzn_id)
                    if not df_amzn.empty:
                        m_amzn = pd.merge(df_master, df_amzn, on='id', how='left')
                        ghosts_amzn = m_amzn[m_amzn['amount_amazon'].isna()]
                        if not ghosts_amzn.empty:
                            st.error(f"⚠️ Flagged {len(ghosts_amzn)} marketplace transactions missing from Amazon panels.")
                            st.dataframe(ghosts_amzn[['id', 'amount_store']], use_container_width=True)
                            leaks_detected += len(ghosts_amzn)
                        else: st.success("✅ Amazon Marketplace matches the Master File perfectly.")
                tab_idx += 1

            # Render Executive Dashboard Top Summaries
            st.markdown("### 📈 Diagnostic Summary Panels")
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("Master Hub Ingested", f"{len(df_master)} Orders")
            with m2: st.metric("System-Wide Revenue Leaks", f"{leaks_detected} Flagged Rows", delta=f"-{leaks_detected}" if leaks_detected > 0 else "0", delta_color="inverse")
            with m3: st.metric("Spoke Nodes Evaluated", f"{tab_idx} Active Channels")

else:
    st.markdown("<div style='background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; color: #8b949e;'>💡 <b>System Standby:</b> Please establish your core basis metrics by uploading your Master Storefront File or activating the Shopify Live API integration on the left sidebar context panels.</div>", unsafe_allow_html=True)

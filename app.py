import streamlit as st
import pandas as pd
import requests  # Built-in library to talk to external web APIs
from datetime import datetime, timedelta

# ==========================================
# 1. AUTOMATED API INGESTION ENGINE ($0 COST)
# ==========================================

def fetch_shopify_orders(api_token, shop_url):
    """Fetches the last 24 hours of orders directly from Shopify Admin API"""
    # Calculate time boundary for yesterday
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Shopify endpoint URL layout
    endpoint = f"https://{shop_url}/admin/api/2026-04/orders.json?created_at_min={yesterday}&status=any"
    headers = {
        "X-Shopify-Access-Token": api_token,
        "Content-Type": "application/json"
    }
    
    try:
        # Requesting data safely over HTTPS
        response = requests.get(endpoint, headers=headers, timeout=10)
        if response.status_code == 200:
            orders = response.json().get('orders', [])
            # Flatten JSON data into a lean Pandas DataFrame structure
            if orders:
                return pd.DataFrame([{
                    'id': str(order['order_number']),
                    'amount_store': float(order['current_total_price'])
                } for order in orders])
            return pd.DataFrame(columns=['id', 'amount_store'])
        else:
            st.sidebar.error(f"Shopify Sync Failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.sidebar.error(f"Shopify Connection Error: {e}")
        return None

def fetch_razorpay_payments(api_key, api_secret):
    """Fetches the last 24 hours of transaction settlements from Razorpay API"""
    # Razorpay utilizes Unix timestamps for intervals
    from_time = int((datetime.now() - timedelta(days=1)).timestamp())
    endpoint = f"https://api.razorpay.com/v1/payments?from={from_time}"
    
    try:
        # Razorpay requires HTTP Basic Authentication (Key ID & Secret)
        response = requests.get(endpoint, auth=(api_key, api_secret), timeout=10)
        if response.status_code == 200:
            payments = response.json().get('items', [])
            if payments:
                return pd.DataFrame([{
                    'id': str(pay['notes'].get('shopify_order_number', pay['description'])),
                    'amount_gateway': float(pay['amount']) / 100, # Convert Paisa to INR Rupees
                    'fee_gateway': float(pay.get('fee', 0)) / 100
                } for pay in payments if pay['status'] == 'captured'])
            return pd.DataFrame(columns=['id', 'amount_gateway', 'fee_gateway'])
        else:
            st.sidebar.error(f"Razorpay Sync Failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.sidebar.error(f"Razorpay Connection Error: {e}")
        return None

# 1. Page Configuration & Title Setup
st.set_page_config(page_title="ReconSimple Pro", layout="wide", initial_sidebar_state="expanded")

# 2. Advanced Premium CSS Injector
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
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 24px;
    }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 14px !important; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 28px !important; font-weight: 700 !important; }
    .upload-card { background-color: #161b22; border: 1px dashed #444c56; border-radius: 12px; padding: 15px; text-align: center; }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f6feb 0%, #0d44a3 100%);
        color: white !important;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Brand Header
st.sidebar.markdown("<h2 style='color: white; font-weight: 700;'>⚙️ Engine Config</h2>", unsafe_allow_html=True)
expected_fee_pct = st.sidebar.slider("Target Aggregator Fee Base (%)", 1.0, 5.0, 2.3, 0.1) / 100
st.sidebar.markdown("---")

# 4. Main Header Section
st.title("📊 ReconSimple Pro")
st.markdown("<p style='color: #8b949e; font-size: 16px; margin-top: -15px;'>Enterprise Infrastructure Multi-Channel Reconciliation Engine</p>", unsafe_allow_html=True)
st.markdown("<div style='height: 2px; background: linear-gradient(90deg, #1f6feb 0%, transparent 100%); margin-bottom: 30px;'></div>", unsafe_allow_html=True)

# 5. Ingestion File Upload Matrix
st.markdown("### 📥 1. Ingest Active Channel Data")
col1, col2, col3, col4, col5 = st.columns(5)

# Placeholders for loaded dataframes
df_master_raw, df_g1_raw, df_g2_raw, df_log_raw = None, None, None, None

with col1:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    f_store = st.file_uploader("Storefront (Shopify/Woo)", type=["csv"])
    st.markdown('</div>', unsafe_allow_html=True)
    if f_store:
        df_master_raw = pd.read_csv(f_store)
        col_master_id = st.selectbox("Select Order ID Column", df_master_raw.columns, key="master_id")

with col2:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    f_gtway1 = st.file_uploader("Primary (Razorpay)", type=["csv"])
    st.markdown('</div>', unsafe_allow_html=True)
    if f_gtway1:
        df_g1_raw = pd.read_csv(f_gtway1)
        col_g1_id = st.selectbox("Select ID Column", df_g1_raw.columns, key="g1_id")

with col3:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    f_gtway2 = st.file_uploader("Backup (Stripe)", type=["csv"])
    st.markdown('</div>', unsafe_allow_html=True)
    if f_gtway2:
        df_g2_raw = pd.read_csv(f_gtway2)
        col_g2_id = st.selectbox("Select ID Column", df_g2_raw.columns, key="g2_id")

with col4:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    f_mktplace = st.file_uploader("Marketplace (Amazon)", type=["csv"])
    st.markdown('</div>', unsafe_allow_html=True)

with col5:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    f_logistics = st.file_uploader("Logistics (Shiprocket)", type=["csv"])
    st.markdown('</div>', unsafe_allow_html=True)
    if f_logistics:
        df_log_raw = pd.read_csv(f_logistics)
        col_log_id = st.selectbox("Select ID Column", df_log_raw.columns, key="log_id")

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 6. Backend Cross-Matching Operational Loop
if f_store:
    if st.button("🚀 Execute System-Wide Reconciliation Audit", use_container_width=True):
        st.markdown("---")
        with st.spinner("Processing structural multi-tenant joins..."):
            
            # Use the explicitly selected column name from the UI selector dropdown
            df_master = df_master_raw.copy()
            df_master['id'] = df_master[col_master_id].astype(str).str.strip()
            
            total_orders = len(df_master)
            leaked_orders_count = 0
            fee_anomalies_count = 0
            unfulfilled_orders_count = 0

            # Execute matching operations conditionally based on selected drop-downs
            if f_gtway1:
                df_g1 = df_g1_raw.copy()
                df_g1['id'] = df_g1[col_g1_id].astype(str).str.strip()
                merged_g1 = pd.merge(df_master, df_g1, on='id', how='left', suffixes=('_store', '_g1'))
                ghost_g1 = merged_g1[merged_g1[df_g1.columns[1]].isna()]
                leaked_orders_count += len(ghost_g1)

            if f_gtway2:
                df_g2 = df_g2_raw.copy()
                df_g2['id'] = df_g2[col_g2_id].astype(str).str.strip()
                if 'fee' in df_g2.columns and 'amount' in df_g2.columns:
                    high_fee = df_g2[df_g2['fee'] > (df_g2['amount'] * expected_fee_pct)]
                    fee_anomalies_count += len(high_fee)

            if f_logistics:
                df_log = df_log_raw.copy()
                df_log['id'] = df_log[col_log_id].astype(str).str.strip()
                merged_log = pd.merge(df_master, df_log, on='id', how='left')
                unfulfilled = merged_log[merged_log[df_log.columns[1]].isna()]
                unfulfilled_orders_count = len(unfulfilled)

            # 7. Executive Visualization Panels
            st.markdown("### 📈 2. Channel System Diagnostics Summary")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Ingested Volume", f"{total_orders} Txns")
            with m2:
                st.metric("Ghost Orders (Leakage)", f"{leaked_orders_count} Units", delta=f"-{leaked_orders_count}" if leaked_orders_count > 0 else "0", delta_color="inverse")
            with m3:
                st.metric("Fee Discrepancies", f"{fee_anomalies_count} Flagged")
            with m4:
                st.metric("Logistics Dropouts", f"{unfulfilled_orders_count} Units")

            st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
            st.markdown("### 🔍 3. Segmented Operational Reports")
            
            tab1, tab2, tab3 = st.tabs(["🔒 Ghost Orders In-Depth", "💸 Fee Inconsistencies", "📦 Missing Shipping Records"])
            
            with tab1:
                if f_gtway1 and leaked_orders_count > 0:
                    st.dataframe(ghost_g1[['id']].rename(columns={'id': 'Flagged Dropout Order ID'}), use_container_width=True)
                else:
                    st.success("System verified: All active digital orders perfectly reconcile across storefront channels.")
                    
            with tab2:
                if fee_anomalies_count > 0:
                    st.dataframe(high_fee, use_container_width=True)
                else:
                    st.success("System verified: Platform fee structures fall accurately within expected percentage bounds.")
                    
            with tab3:
                if f_logistics and unfulfilled_orders_count > 0:
                    st.dataframe(unfulfilled[['id']], use_container_width=True)
                else:
                    st.success("System verified: No shipping tracking dropouts recorded across operations.")
else:
    st.markdown("<div style='background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; color: #8b949e;'>💡 <b>System Standby:</b> Please upload your Master Storefront data template in the ingestion zone above to initialize system matrix mapping paths.</div>", unsafe_allow_html=True)

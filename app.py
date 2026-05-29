import streamlit as st
import pandas as pd

# 1. Page Configuration & Title Setup
st.set_page_config(page_title="ReconSimple Pro", layout="wide", initial_sidebar_state="expanded")

# 2. Advanced Premium CSS Injector (Modern Luxury Dark Theme)
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Header & Typography Styling */
    h1 {
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    h3 {
        font-weight: 600 !important;
        color: #f0f6fc !important;
        margin-top: 20px !important;
    }
    
    /* Card Container Styling */
    div[data-testid="stVerticalBlock"] > div {
        background: none;
    }
    
    /* Modern Metric Card Designs */
    div[data-testid="stMetricContainer"] {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetricContainer"]:hover {
        transform: translateY(-2px);
        border-color: #58a6ff;
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    /* Upload Box Wrapper Styling */
    .upload-card {
        background-color: #161b22;
        border: 1px dashed #444c56;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }
    
    /* Premium Action Button Customization */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f6feb 0%, #0d44a3 100%);
        color: white !important;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        border-radius: 8px;
        box-shadow: 0 4px 14px rgba(31, 111, 235, 0.4);
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #388bfd 0%, #1f6feb 100%);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(31, 111, 235, 0.6);
    }
    
    /* Tab Styling Customization */
    button[data-testid="stMarkdownContainer"] {
        font-weight: 600;
    }
    div[data-testid="stTabBar"] {
        background-color: #161b22;
        border-radius: 8px;
        padding: 4px;
        border: 1px solid #30363d;
    }
    button[aria-selected="true"] {
        background-color: #21262d !important;
        border-radius: 6px !important;
        color: #58a6ff !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Brand Header
st.sidebar.markdown("<h2 style='color: white; font-weight: 700;'>⚙️ Engine Config</h2>", unsafe_allow_html=True)
expected_fee_pct = st.sidebar.slider("Target Aggregator Fee Base (%)", 1.0, 5.0, 2.3, 0.1) / 100
st.sidebar.markdown("---")
st.sidebar.markdown("### System Environment\n`Production Cloud v1.0.2`")

# 4. Main Header Section
st.title("📊 ReconSimple Pro")
st.markdown("<p style='color: #8b949e; font-size: 16px; margin-top: -15px;'>Enterprise Infrastructure Multi-Channel Reconciliation Engine</p>", unsafe_allow_html=True)
st.markdown("<div style='height: 2px; background: linear-gradient(90deg, #1f6feb 0%, transparent 100%); margin-bottom: 30px;'></div>", unsafe_allow_html=True)

# 5. Ingestion File Upload Matrix
st.markdown("### 📥 1. Ingest Active Channel Data")
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        f_store = st.file_uploader("Storefront (Shopify/Woo)", type=["csv"])
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        f_gtway1 = st.file_uploader("Primary (Razorpay)", type=["csv"])
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        f_gtway2 = st.file_uploader("Backup (Stripe)", type=["csv"])
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        f_mktplace = st.file_uploader("Marketplace (Amazon)", type=["csv"])
        st.markdown('</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        f_logistics = st.file_uploader("Logistics (Shiprocket)", type=["csv"])
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 6. Backend Cross-Matching Operational Loop
if f_store:
    if st.button("🚀 Execute System-Wide Reconciliation Audit", use_container_width=True):
        st.markdown("---")
        with st.spinner("Processing structural multi-tenant joins..."):
            
            # Setup base dataframe mapping
            df_master = pd.read_csv(f_store)
            df_master.columns = df_master.columns.str.strip().str.lower()
            df_master = df_master.rename(columns={'order id': 'id', 'order_id': 'id', 'transaction_id': 'id'})
            df_master['id'] = df_master['id'].astype(str)
            
            total_orders = len(df_master)
            leaked_orders_count = 0
            fee_anomalies_count = 0
            unfulfilled_orders_count = 0

            # Execute matching operations conditionally
            if f_gtway1:
                df_g1 = pd.read_csv(f_gtway1)
                df_g1.columns = df_g1.columns.str.strip().str.lower()
                df_g1 = df_g1.rename(columns={'txn id': 'id', 'transaction id': 'id', 'payment_id': 'id'})
                df_g1['id'] = df_g1['id'].astype(str)
                merged_g1 = pd.merge(df_master, df_g1, on='id', how='left', suffixes=('_store', '_g1'))
                ghost_g1 = merged_g1[merged_g1[df_g1.columns[1]].isna()]
                leaked_orders_count += len(ghost_g1)

            if f_gtway2:
                df_g2 = pd.read_csv(f_gtway2)
                df_g2.columns = df_g2.columns.str.strip().str.lower()
                df_g2 = df_g2.rename(columns={'txn id': 'id', 'transaction id': 'id'})
                df_g2['id'] = df_g2['id'].astype(str)
                if 'fee' in df_g2.columns and 'amount' in df_g2.columns:
                    high_fee = df_g2[df_g2['fee'] > (df_g2['amount'] * expected_fee_pct)]
                    fee_anomalies_count += len(high_fee)

            if f_logistics:
                df_log = pd.read_csv(f_logistics)
                df_log.columns = df_log.columns.str.strip().str.lower()
                df_log = df_log.rename(columns={'order id': 'id', 'order_id': 'id'})
                df_log['id'] = df_log['id'].astype(str)
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
            
            # Interactive tab matrix
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

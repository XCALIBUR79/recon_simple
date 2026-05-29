import streamlit as st
import pandas as pd

# Set page configuration for a premium look
st.set_page_config(page_title="ReconSimple Pro", layout="wide", initial_sidebar_state="expanded")

# Custom CSS styling for metric containers
st.markdown("""
    <style>
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    div[data-testid="stMetricContainer"] { background-color: #1e222b; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 ReconSimple Pro")
st.subheader("Multi-Channel Financial Reconciliation & Leakage Audit Engine")
st.markdown("---")

# Sidebar configurations
st.sidebar.header("Audit Controls")
expected_fee_pct = st.sidebar.slider("Expected Aggregator Fee (%)", 1.0, 5.0, 2.0, 0.1) / 100

# Step 1: Create 5 Clean Upload Containers
st.markdown("### 📥 Step 1: Ingest Channel Data Sources")
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        f_store = st.file_uploader("Storefront (Shopify/Woo)", type=["csv"])
    with col2:
        f_gtway1 = st.file_uploader("Primary Gateway (Razorpay)", type=["csv"])
    with col3:
        f_gtway2 = st.file_uploader("Backup Gateway (Stripe)", type=["csv"])
    with col4:
        f_mktplace = st.file_uploader("Marketplace (Amazon)", type=["csv"])
    with col5:
        f_logistics = st.file_uploader("Logistics (Shiprocket)", type=["csv"])

# Step 2: Processing Engine
if f_store:
    if st.button("🚀 Execute Multi-Channel Cross-Match Audit", use_container_width=True):
        with st.spinner("Executing structural outer-joins across all active channels..."):
            
            # Read Core Storefront File (The Master Hub)
            df_master = pd.read_csv(f_store)
            df_master.columns = df_master.columns.str.strip().str.lower()
            df_master = df_master.rename(columns={'order id': 'id', 'order_id': 'id', 'transaction_id': 'id'})
            df_master['id'] = df_master['id'].astype(str)
            
            total_orders = len(df_master)
            total_revenue = df_master.iloc[:, 1].sum() if len(df_master.columns) > 1 else 0
            
            # Tracking variables for reporting
            leaked_orders_count = 0
            fee_anomalies_count = 0
            unfulfilled_orders_count = 0

            # -------------------------------------------------------------
            # Channel 2: Primary Gateway (Razorpay) Comparison
            # -------------------------------------------------------------
            if f_gtway1:
                df_g1 = pd.read_csv(f_gtway1)
                df_g1.columns = df_g1.columns.str.strip().str.lower()
                df_g1 = df_g1.rename(columns={'txn id': 'id', 'transaction id': 'id', 'payment_id': 'id'})
                df_g1['id'] = df_g1['id'].astype(str)
                
                # Merge logic
                merged_g1 = pd.merge(df_master, df_g1, on='id', how='left', suffixes=('_store', '_g1'))
                ghost_g1 = merged_g1[merged_g1[df_g1.columns[1]].isna()]
                leaked_orders_count += len(ghost_g1)

            # -------------------------------------------------------------
            # Channel 3: Backup Gateway (Stripe) Comparison
            # -------------------------------------------------------------
            if f_gtway2:
                df_g2 = pd.read_csv(f_gtway2)
                df_g2.columns = df_g2.columns.str.strip().str.lower()
                df_g2 = df_g2.rename(columns={'txn id': 'id', 'transaction id': 'id'})
                df_g2['id'] = df_g2['id'].astype(str)
                
                merged_g2 = pd.merge(df_master, df_g2, on='id', how='left')
                # Simple flag logic example for high fees
                if 'fee' in df_g2.columns and 'amount' in df_g2.columns:
                    high_fee = df_g2[df_g2['fee'] > (df_g2['amount'] * expected_fee_pct)]
                    fee_anomalies_count += len(high_fee)

            # -------------------------------------------------------------
            # Channel 5: Logistics Tracker (Shiprocket Cod/Prepaid matching)
            # -------------------------------------------------------------
            if f_logistics:
                df_log = pd.read_csv(f_logistics)
                df_log.columns = df_log.columns.str.strip().str.lower()
                df_log = df_log.rename(columns={'awb': 'id', 'order id': 'id', 'order_id': 'id'})
                df_log['id'] = df_log['id'].astype(str)
                
                merged_log = pd.merge(df_master, df_log, on='id', how='left')
                unfulfilled = merged_log[merged_log[df_log.columns[1]].isna()]
                unfulfilled_orders_count = len(unfulfilled)

            # -------------------------------------------------------------
            # Step 3: High-End Visualizations & Executive Summary
            # -------------------------------------------------------------
            st.markdown("### 📈 Step 2: System Health & Executive Summary")
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Ingested Orders", f"{total_orders}", help="Total unique orders registered in storefront database")
            with m2:
                st.metric("Ghost Orders (Revenue Leak)", f"{leaked_orders_count}", delta=f"-{leaked_orders_count}" if leaked_orders_count > 0 else "0", delta_color="inverse")
            with m3:
                st.metric("Fee Rule Violations", f"{fee_anomalies_count}", delta=f"{fee_anomalies_count} flagged" if fee_anomalies_count > 0 else "0", delta_color="off")
            with m4:
                st.metric("Unshipped / Lost Orders", f"{unfulfilled_orders_count}", help="Orders paid for but missing from logistics logs")

            st.markdown("### 🔍 Step 3: Granular Channel Overviews")
            
            # Tabbed interface to separate messy multi-file results cleanly
            tab1, tab2, tab3 = st.tabs(["Ghost Orders Analysis", "Fee Deviations", "Logistics Discrepancies"])
            
            with tab1:
                st.subheader("Storefront vs Payment Gateways Dropouts")
                if f_gtway1 and leaked_orders_count > 0:
                    st.dataframe(ghost_g1[['id']].rename(columns={'id': 'Flagged Order ID'}), use_container_width=True)
                else:
                    st.success("No multi-channel order dropouts discovered.")
                    
            with tab2:
                st.subheader("Processor Fee Anomalies")
                if fee_anomalies_count > 0:
                    st.dataframe(high_fee, use_container_width=True)
                else:
                    st.success("All processor transactions settle within your expected percentage variance thresholds.")
                    
            with tab3:
                st.subheader("Storefront vs Courier Matching")
                if f_logistics and unfulfilled_orders_count > 0:
                    st.dataframe(unfulfilled[['id']], use_container_width=True)
                else:
                    st.success("All processed sales have corresponding tracking information generated.")
else:
    st.info("💡 To begin, upload at least your Master Storefront data file to populate the hub framework.")

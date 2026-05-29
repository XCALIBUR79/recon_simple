import streamlit as st
import pandas as pd
from pydantic import BaseModel, ValidationError
from datetime import datetime

# 1. THE GATEKEEPER: Define what perfect data looks like
class CleanTransaction(BaseModel):
    transaction_id: str
    amount: float

# 2. THE ENGINE: Match the files and find the gaps
def run_reconciliation(sales_df, gateway_df):
    # Standardize column names to lowercase and remove spaces
    sales_df.columns = sales_df.columns.str.strip().str.lower()
    gateway_df.columns = gateway_df.columns.str.strip().str.lower()

    # Rename columns to match our logic if they use common variations
    sales_df = sales_df.rename(columns={'order id': 'transaction_id', 'id': 'transaction_id', 'order_id': 'transaction_id'})
    gateway_df = gateway_df.rename(columns={'txn id': 'transaction_id', 'transaction id': 'transaction_id', 'payment_id': 'transaction_id'})

    # Ensure transaction IDs are strings
    sales_df['transaction_id'] = sales_df['transaction_id'].astype(str)
    gateway_df['transaction_id'] = gateway_df['transaction_id'].astype(str)

    # Merge the two files using an Outer Join
    merged = pd.merge(sales_df, gateway_df, on="transaction_id", how="outer", suffixes=("_store", "_gateway"))

    # Find orders that exist in the store but have NO payment in the gateway
    missing_payouts = merged[merged["amount_gateway"].isna() & merged["amount_store"].notna()]
    
    return missing_payouts

# 3. THE INTERFACE: Build the web page layout
st.set_page_config(page_title="ReconSimple", layout="wide")
st.title("📊 ReconSimple")
st.subheader("Identify Multi-Channel Fee Leakage & Missing Orders Instantly")

st.markdown("---")

# File Upload Columns
col1, col2 = st.columns(2)
with col1:
    uploaded_sales = st.file_uploader("1. Upload Store Orders (Shopify/WooCommerce CSV)", type=["csv"])
with col2:
    uploaded_gateway = st.file_uploader("2. Upload Payment Gateway Settlements (Razorpay/Stripe CSV)", type=["csv"])

# Run Analysis Button
if uploaded_sales and uploaded_gateway:
    if st.button("🚀 Run Margin Audit", use_container_width=True):
        with st.spinner("Analyzing files for data discrepancies..."):
            try:
                # Load files into memory
                df_sales = pd.read_csv(uploaded_sales)
                df_gateway = pd.read_csv(uploaded_gateway)

                # Process the data
                missing_data = run_reconciliation(df_sales, df_gateway)

                # Display Results
                st.markdown("### 🔍 Audit Results")
                if len(missing_data) > 0:
                    st.error(f"⚠️ Found {len(missing_data)} Ghost Orders! These orders exist in your store but no payment was recorded in your gateway.")
                    st.dataframe(missing_data[['transaction_id', 'amount_store']])
                else:
                    st.success("✅ Perfect Match! All storefront orders successfully match your payment gateway settlements.")

            except Exception as e:
                st.error(f"Error parsing files: Check if your CSV files contain 'transaction_id' and 'amount' columns. Detailed error: {e}")
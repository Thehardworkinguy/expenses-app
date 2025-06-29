import streamlit as st
import pandas as pd
import re

# Page configuration
st.set_page_config(page_title="HDFC Excel Statement Viewer", layout="wide")
st.title("📊 HDFC Excel Statement Viewer")

# File upload
uploaded_file = st.file_uploader(
    "Upload your HDFC bank statement (Excel)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Read entire Excel file to find the actual header row
        raw_df = pd.read_excel(uploaded_file, engine="openpyxl", header=None)

        # Detect the header row that contains both 'Date' and 'Narration'
        header_row_index = None
        for idx, row in raw_df.iterrows():
            values = row.astype(str).str.lower().tolist()
            if "date" in values and "narration" in values:
                header_row_index = idx
                break

        if header_row_index is None:
            st.error("❌ Could not find header row with both 'Date' and 'Narration'")
            st.stop()

        # Load the actual transaction DataFrame
        df = pd.read_excel(uploaded_file, engine="openpyxl",
                           header=header_row_index)

        st.success("✅ Excel file uploaded and processed successfully!")

        # Show transaction data
        st.subheader("📋 Transaction Data")
        st.dataframe(df, use_container_width=True)

        # Filter only withdrawal rows with valid narration
        df_clean = df[['Narration', 'Withdrawal Amt.']].dropna()
        df_clean['Narration'] = df_clean['Narration'].astype(
            str).str.upper().str.strip()

        # Extract UPI Merchant Name (e.g., "UPI-PAYTM-XYZ" → "PAYTM")
        def extract_upi_merchant(narration):
            match = re.search(r'UPI-(.*?)-', narration.upper())
            return match.group(1).strip() if match else None

        df_clean['UPI_Merchant'] = df_clean['Narration'].apply(
            extract_upi_merchant)
        df_upi = df_clean.dropna(subset=['UPI_Merchant'])

        if df_upi.empty:
            st.warning("⚠️ No UPI transactions found.")
        else:
            # Group by UPI Merchant and calculate total spent
            upi_summary = df_upi.groupby('UPI_Merchant')[
                'Withdrawal Amt.'].sum().sort_values(ascending=False)

            # Display Top Spending UPI Merchant
            top_merchant = upi_summary.idxmax()
            top_amount = upi_summary.max()

            st.subheader("🏆 Top UPI Spending")
            st.markdown(f"**🔍 Most spent on UPI Merchant:** `{top_merchant}`")
            st.markdown(f"**💸 Total amount spent:** ₹{top_amount:,.2f}")

            # Full summary
            with st.expander("🔽 View all UPI spending by merchant"):
                st.dataframe(upi_summary.reset_index().rename(
                    columns={"UPI_Merchant": "Merchant", "Withdrawal Amt.": "Total Spent (₹)"}))
            total_upi_spent = upi_summary.sum()
            st.markdown(
                f"**🧾 Total UPI Spend (All Merchants):** ₹{total_upi_spent:,.2f}")

    except Exception as e:
        st.error(f"❌ Failed to process the Excel file: {e}")

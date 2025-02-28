import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import openpyxl

# Load or Generate Dataset
def generate_sample_data():
    np.random.seed(42)
    projects = ["Airtel", "TataSky", "Vodafone"]
    content_types = ["Sports", "Movies", "Kids", "News"]
    ad_providers = ["Google Ads", "Facebook Ads", "Amazon Ads", "Local Sponsor"]
    
    data = {
        "Project": np.random.choice(projects, 500),
        "Content_Type": np.random.choice(content_types, 500),
        "Ad_Duration": np.random.randint(5, 120, 500),
        "Ad_Provider": np.random.choice(ad_providers, 500),
        "Watch_Time": np.random.uniform(0.2, 1.0, 500),
        "Bitrate_Drop": np.random.choice(["Yes", "No"], 500, p=[0.2, 0.8]),
        "Skipped_Ads": np.random.choice(["Yes", "No"], 500, p=[0.3, 0.7]),
        "CPM_Revenue": np.random.uniform(0.5, 10.0, 500),
    }
    return pd.DataFrame(data)

df = generate_sample_data()

# Streamlit App UI
st.title("📊 Ad Metrics & Transport Stream Analysis Dashboard")

# Filters
selected_project = st.multiselect("Select Project", df["Project"].unique(), default=df["Project"].unique())
selected_content = st.multiselect("Select Content Type", df["Content_Type"].unique(), default=df["Content_Type"].unique())

df_filtered = df[(df["Project"].isin(selected_project)) & (df["Content_Type"].isin(selected_content))]

# Insights
st.subheader("🔍 Key Insights")
st.write(f"Total Ads: {len(df_filtered)}")
st.write(f"Average Watch Time: {df_filtered['Watch_Time'].mean():.2f}")
st.write(f"Average Ad Revenue: ${df_filtered['CPM_Revenue'].mean():.2f}")

# Visualizations
st.subheader("📈 Ad Duration Distribution")
fig, ax = plt.subplots()
sns.histplot(df_filtered["Ad_Duration"], bins=30, kde=True, ax=ax)
st.pyplot(fig)

st.subheader("📉 Ad Skipped vs. Watched")
fig, ax = plt.subplots()
sns.countplot(data=df_filtered, x="Skipped_Ads", ax=ax)
st.pyplot(fig)

st.subheader("💰 CPM Revenue by Project")
fig, ax = plt.subplots()
sns.boxplot(data=df_filtered, x="Project", y="CPM_Revenue", ax=ax)
st.pyplot(fig)

# Generate Excel Report
def generate_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Ad Metrics', index=False)
    writer.close()
    return output.getvalue()

if st.button("📥 Download Report"):
    excel_data = generate_excel(df_filtered)
    st.download_button(label="Download Excel Report", data=excel_data, file_name="Ad_Metrics_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.success("🚀 Dashboard Ready! Analyze and Optimize Your Ad Metrics!")

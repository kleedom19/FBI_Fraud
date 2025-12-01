"""
Streamlit app for FBI Fraud Data Visualization Dashboard.
"""

import streamlit as st
from fraud_visualizations import (
    get_all_analyses,
    get_summary_stats,
    create_losses_by_category_chart,
    create_losses_by_age_group_chart,
    create_losses_trend_chart,
    create_victims_by_age_group_chart,
    create_category_comparison_chart,
    create_state_visualization
)

# Page configuration
st.set_page_config(
    page_title="FBI Fraud Data Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and header
st.title("FBI Fraud Data Analysis Dashboard")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Dashboard Controls")
    st.markdown("---")
    
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### About")
    st.info(
        "This dashboard visualizes fraud-related data from FBI reports "
        "analyzed using OCR and Gemini AI. Data is stored in Supabase."
    )

# Load data with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_analyses():
    """Load all analyses from Supabase."""
    return get_all_analyses()

# Fetch data
with st.spinner("Loading data from Supabase..."):
    all_analyses = load_analyses()

if not all_analyses:
    st.error("No data found in Supabase. Please run `analyze_ocr.py` first to process OCR files.")
    st.stop()

# Summary statistics
st.header("Summary Statistics")
stats = get_summary_stats(all_analyses)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Losses",
        value=f"${stats.get('total_loss', 0):,.0f}" if stats.get('total_loss') else "N/A"
    )

with col2:
    st.metric(
        label="Total Victims",
        value=f"{stats.get('total_victims', 0):,}" if stats.get('total_victims') else "N/A"
    )

with col3:
    st.metric(
        label="Years Covered",
        value=", ".join(map(str, stats.get('years_covered', []))) if stats.get('years_covered') else "N/A"
    )

with col4:
    st.metric(
        label="Documents Analyzed",
        value=stats['total_documents']
    )

st.markdown("---")

# Main visualizations
st.header("Fraud Analysis Visualizations")

# Financial Losses Trends
st.subheader("Fraud Trends Over Time")
trends_fig = create_losses_trend_chart(all_analyses)
if trends_fig:
    st.plotly_chart(trends_fig, use_container_width=True)
else:
    st.warning("Not enough data for trend analysis. Please ensure Gemini extracted fraud metrics from the documents.")

st.markdown("---")

# Top Fraud Categories
st.subheader("Top Fraud Categories by Financial Loss")
category_fig = create_losses_by_category_chart(all_analyses)
if category_fig:
    st.plotly_chart(category_fig, use_container_width=True)
else:
    st.warning("No fraud category data available. Please ensure documents contain fraud category information.")

st.markdown("---")

# Two column layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Financial Losses by Age Group")
    age_loss_fig = create_losses_by_age_group_chart(all_analyses)
    if age_loss_fig:
        st.plotly_chart(age_loss_fig, use_container_width=True)
    else:
        st.warning("No age group data available.")

with col2:
    st.subheader("Victim Counts by Age Group")
    age_victim_fig = create_victims_by_age_group_chart(all_analyses)
    if age_victim_fig:
        st.plotly_chart(age_victim_fig, use_container_width=True)
    else:
        st.warning("No victim count data available.")

st.markdown("---")

# Category Comparison
st.subheader("Top Fraud Categories: Year-over-Year Comparison")
comparison_fig = create_category_comparison_chart(all_analyses)
if comparison_fig:
    st.plotly_chart(comparison_fig, use_container_width=True)
else:
    st.warning("Not enough category data across multiple years for comparison.")

st.markdown("---")

# State Visualization
st.subheader("Fraud Incidents by State")
state_fig = create_state_visualization(all_analyses)
if state_fig:
    st.plotly_chart(state_fig, use_container_width=True)
else:
    st.warning("No state data available. State information may not be present in the analyzed documents.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "FBI Fraud Data Analysis Dashboard | Powered by Gemini AI & Supabase"
    "</div>",
    unsafe_allow_html=True
)


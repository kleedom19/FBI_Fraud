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
from dotenv import load_dotenv
load_dotenv()

import os
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

st.markdown("""
    <style>
        .top-banner {
            width: 100%;
            background-color: #C8DAB9;
            padding: 25px 0;
            text-align: center;
            font-size: 26px;
            font-weight: bold;
            color: black;
            border-radius: 6px;
            margin-bottom: 25px;
        }
        /* Section container */
        .sage-box {
            background-color: #E6F0D9;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }

        /* Styled subheaders inside columns */
        .soft-subheader {
            background-color: #E6F0D9;  /* Lighter sage green */
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        /* Styled sub-subheader */
        .soft-subsubheader {
            background-color:#E6F0D9;
            padding:10px;
            border-radius:10px;
            text-align:left;
            font-size:17px;
            font-weight:500;
            color:#3a3a3a;
            margin-top:5px;
            margin-left:10px;
        }
        /* Image border */
        .sage-image {
            border-radius: 10px;
            border: 3px solid #C8DAB9;
        }
        /*Thin line to break sections up*/
        .thin-line {
            border: 0.5px solid #cccccc;
            margin: 10px 0;
        }
    </style>
    <div class="top-banner">
        FBI Fraud Data Dashboard
    </div>
""", unsafe_allow_html=True)

st.set_page_config(layout="wide", page_title="Findings", page_icon="📊")

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

st.write("""
We analyzed data from the FBI's Annual Internet Crime Data Reports from 2019 - 2021, and studied the most popular fraud schemes that target people 60 years and older, as well as general fraud trends. This data allows us to learn which fraud types to warn this group of people about to help midigate the amount of money lost each year due to fraud in this age bracket.
""")

# Summary statistics
st.markdown("<div class='soft-subheader'>Summary Statistics</div>", unsafe_allow_html=True)
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

col1, col2 = st.columns([1, 1])


with col1:
    st.markdown("<div class='soft-subheader'>Total Financial Loss By Age Group</div>", unsafe_allow_html=True)
    st.write("""
    This visualization shows data from 20xx - 20xx and graphs financial loss totals due to scams and fraud by age group. The color scale shows viewers darker blues indicate higher amounts of money lost.
    
    Adults over 60 had the highest total amount lost, exceeding just over $1.8 billion, making them the most financially impacted group.
    
    Losses gradualy decline with younger groups, with the exception of 20-29 being the lowest at only $375 million lost.
             
    These findings show that those 60 and older are--------
    """)
   
    st.markdown('</div>', unsafe_allow_html=True)


with col2:
    age_loss_fig = create_losses_by_age_group_chart(all_analyses)
    if age_loss_fig:
        st.plotly_chart(age_loss_fig, use_container_width=True)
    else:
        st.warning("No age group data available.")


col3, col4 = st.columns([1, 1])


with col3:
    st.markdown("<div class='soft-subheader'>Victim Counts by Age Group</div>", unsafe_allow_html=True)
    st.write("""
    The chart shows how many people in each age group were victims of a fraud scheme.
    
    Adults over 60 are shown to have the highest amount of victims at just over 173,000 reported, with adults 30-59 reporting similar numbers around 140,000. Age group 20-29 shows a noticable drop to 115,000 victims and under 20 only reporting 33,000 cases.
    
    These findings show fraud scheme education needs to be taught to adults of all ages, especially those over 60, on what to look out for that could be a scam to help reduce these numbers.
    """)
   
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    age_victim_fig = create_victims_by_age_group_chart(all_analyses)
    if age_victim_fig:
        st.plotly_chart(age_victim_fig, use_container_width=True)
    else:
        st.warning("No victim count data available.")

st.markdown("---")



st.markdown("<div class='soft-subheader'>Fraud Incidents by State</div>", unsafe_allow_html=True)
st.markdown("""
    This graphs ranks U.S. states by their total financial loss over 200xx to 20xx.

    California stands out with over $800 million in loss due to fraud. Texas follows behind with $500 million and Florida in third with $390 million.

    While these three states have larger populations that others, banks are still interested in which states the most fraudulent activity occurs in. Transactions done in these states may be monitored more heavily than others in attempt to catch fraud-related money.  
""")

state_fig = create_state_visualization(all_analyses)
if state_fig:
    st.plotly_chart(state_fig, use_container_width=True)
else:
    st.warning("No state data available. State information may not be present in the analyzed documents.")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "FBI Fraud Data Analysis Dashboard | Powered by Gemini AI & Supabase"
    "</div>",
    unsafe_allow_html=True
)


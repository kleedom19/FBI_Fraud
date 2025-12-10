import streamlit as st
import pandas as pd
import supabase
from supabase import create_client, Client
import base64
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

st.set_page_config(layout="wide", page_title="Demonstration", page_icon="📊")

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
        Demonstration Of Our API
    </div>
""", unsafe_allow_html=True)

st.markdown("""
**Let's view the full pipeline from choosing the documents you wish to scrape to creating a visualization with that data**
""")

# ------ STEP 1 ------
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("<div class='soft-subheader'>1) Select Your PDF and Feed It to the API</div>", unsafe_allow_html=True)
    st.write("""
        Users begin by selecting the PDF they wish to scrape and add it to the folder containing `ocr_api.py`.
        
        Go into the terminal and type the following command:
        ```bash
        uv run ocr_api.py .\\your-file.pdf
        ```
        This calls Modal to coldstart, and the PDF will run through the OCR. The Markdown output is returned in a JSON file under the name specified in the code into the same folder.
    
             
        To the right is an example of a PDF we scraped containing elder fraud data from 2022 - 2024.
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:

    with open("imagesForSL/60AndUp.pdf", "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

    pdf_display = f"""
    <iframe 
        src="data:application/pdf;base64,{base64_pdf}" 
        width="100%" 
        height="600px" 
        style="border: none;"
    ></iframe>
    """

    st.markdown(pdf_display, unsafe_allow_html=True)

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div class='soft-subheader'>2) Use Gemini to convert Markdown into a pandas DataFrame</div>", unsafe_allow_html=True)
st.write("""
Our OCR pipeline can run as one unified command from PDF → OCR → Gemini → Supabase, or it can operate as two separate phases for documents containing security-sensitive information.
""")

st.markdown ("""
__Key Files__:
- `client_pipeline.py`: Client script that orchestrates the complete pipeline
    -`analyze_ocr.py`: Standalone script to analyze OCR output with Gemini and save to Supabase - no Modal required.
- `analyze_server.py`: Standalone FastAPI server for Gemini analysis and Supabase storage - no Modal required.
- `gemini_supabase.py`: Shared module for Gemini analysis and Supabase storage.
""")
st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)
st.markdown("""
**You may choose to**:

- Run the full pipeline automatically (`client_pipeline.py`)
    * Fully hands-off once the PDF is inputted
    * Great for large document batches (containing non-sensitive data)
    * Results are generated and saved the same way each time

            
- Run in Two Steps
    * Run the OCR using `ocr_api.py` to genereate raw JSON file output
    * Use `analyze_ocr.py` to perform the Gemini analysis and interact with the OCR results via command line
         
            
- Run in Two Steps via API 
    * Has the same functionality as above, but was created in the form of API endpoints for easier integration for future scalability
""")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ------ STEP 3 ------
col5, col6 = st.columns([1,1])

supabase: Client = create_client(supabase_url, supabase_key)

# Fetch table
response = supabase.table("ocr_results").select("*").execute()
df = pd.DataFrame(response.data)

with col5:
    st.markdown("<div class='soft-subheader'>3) Load into Supabase</div>", unsafe_allow_html=True)
    st.write("""
        The newly cleaned and formatted data is stored in Supabase tables to be called for further analysis. Once the data is stored, users do not have to run the same files again, which saves on token usage, and it is available to any team member to call on their desired platform.
        
        The raw OCR Markdown data is also saved into tables, allowing for it to be rerun through different queries in Gemini as needed. This adds an extra layer of clarity in how the cleaned data was dervied, as users can view the exact data as it was scraped by the OCR.   
        """)
    
st.markdown("""
    The `key_metrics` column has a Gemini generated one-sentence summary of its findings within the data scraped, including total loses, total victim count, top fraud categories, and the year the data was collected. 

    The `keywords` column displays the most commonly found key words in documents relating to fraud.   
""")


with col6:
    st.dataframe(df, use_container_width=True)

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ------ STEP 4 ------
col7, col8 = st.columns([1,1])

with col7:
    age_loss_fig = create_losses_by_age_group_chart(all_analyses)
    if age_loss_fig:
        st.plotly_chart(age_loss_fig, use_container_width=True)
    else:
        st.warning("No age group data available.")

with col8:
    st.markdown("<div class='soft-subheader'>4) Create Visualizations and Analyze</div>", unsafe_allow_html=True)
    st.write("""
        Utilizing the tables in Supabase, users can call the data to summarize counts, perform a statistical analysis, pull the data into dashboards that update in real time as data is entered, and more.
        
        We show how you can call this data to create visulizations on the 'Findings' tab.
    """)

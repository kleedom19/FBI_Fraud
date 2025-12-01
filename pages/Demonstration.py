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
        This calls Modal to coldstart (this may take a minute) and the PDF will run through the OCR. The Markdown output is returned in a JSON file under the name specified in the code into the same folder.
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # FIX IMAGE IT IS BLURRY
    st.image("imagesForSL/step1.png", width=550, caption="One part of the PDF data we are scraping.")

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ------ STEP 2 ------
col3, col4 = st.columns([1,1])

with col3:
    # ADD IMAGE
    st.image("imagesForSL/gemini.png", width=550, caption="Snippet of the Gemini code")

with col4:
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


st.markdown("""
**Organizations may choose to**:

- Run the full pipeline automatically (`client_pipeline.py`)
    * Fully hands-off once the PDF is inputted
    * Great for large document batches (containing non-sensitive data)
    * Results are generated and saved the same way each time

            
- Run the OCR using Modal (`ocr_api.py`), then send the Markdown into their own private LLM using `analyze_ocr.py`
    * Ideal for documents with sensistive data to comply with company regulations
    * Can swap to prefered LLM for structuring
    * Allows for clarity in how the OCR scraped the data into JSON files (can view raw Markdown)
         
            
- Run the OCR using Modal (`ocr_api.py`), then send the Markdown to the analysis API (`analyze_sever.py`). 
    * Can run on a person's individual system, ensuring all data stays only within your network should you utilize a different OCR model
    * Built in cache review saves on cost of LLM tokens
    * Can update prompts to suit the exact data you're working with
""")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ------ STEP 3 ------
col5, col6 = st.columns([1,1])

with col5:
    st.markdown("<div class='soft-subheader'>3) Load into Supabase</div>", unsafe_allow_html=True)
    st.write("""
        The newly cleaned and formatted data is stored in Supabase tables to be called for further analysis. Once the data is stored, users do not have to run the same files again, which saves on token usage, and it is available to any team member to call on their desired platform.
        
        The raw OCR Markdown data is also saved into tables, allowing for it to be rerun through different queries in Gemini as needed. This adds an extra layer of clarity in how the cleaned data was dervied, as users can view the exact data as it was scraped by the OCR.     """)

with col6:
    # ADD IMAGE
    st.image("imagesForSL/supabase.png", width=550, caption="Snippet of data in Supabase")

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ------ STEP 4 ------
col3, col4 = st.columns([1,1])

with col3:
    # ADD IMAGE
    st.image("imagesForSL/step4.png", width=550, caption="A graph showing total financial loss by age group.")

with col4:
    st.markdown("<div class='soft-subheader'>4) Create Visualizations and Analyze</div>", unsafe_allow_html=True)
    st.write("""
        Utilizing the tables in Supabase, users can call the different tables to display their data on their prefered platform. 
        
        An example of this final step can be found on the 'Findings' tab to the left.
    """)

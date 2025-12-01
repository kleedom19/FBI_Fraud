import streamlit as st

st.set_page_config(layout="wide", page_title="Homepage", page_icon="📊")

# --- TOP BANNER ---
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

        /* Styled subheaders inside columns */
        .soft-subheader {
            background-color: #E6F0D9;  /* Lighter sage green */
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        /* Styled GitHub button */
        .sage-button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #C8DAB9;
            color: black;
            font-size: 16px;
            text-decoration: none;
            border-radius: 8px;
            border: none;
        }
        .flowchart {
            background-color:#E6F0D9;
            padding:20px;
            border-radius:10px;
            text-align:center;
            font-size:18px;
            font-weight:600;
        }
        .sage-button:hover {
            background-color: #B7CBA7;
        }
        .thin-line {
            border: 0.5px solid #cccccc;
            margin: 10px 0;
        }
        /* Section container */
        .sage-box {
            background-color: #E6F0D9;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }

        /* Soft green header*/
        .sage-header {
            background-color: #C8DAB9;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 14px;
            display: inline-block;
        }

        /* Image border */
        .sage-image {
            border-radius: 10px;
            border: 3px solid #C8DAB9;
        }
    </style>

    <div class="top-banner">
        Fraud Detection for Consumers 60+
    </div>              
""", unsafe_allow_html=True)


# --- AUTHOR TEXT ---
st.write("""
**Authors**: Katie Leedom, Jacob German, Rohan Salwekar, Christian Ohlsson

This app introduces our project which aims to build a simple OCR to Gemini pipeline that helps scrape and structure fraud data stored in charts within PDFs for further analysis.
""")

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- TWO COLUMNS ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='soft-subheader'>Key Features</div>", unsafe_allow_html=True)
    st.write("- **OCR**: Deepseek's OCR was used to extract chart-based data efficiently, outputting a JSON file.")
    st.write("- **Gemini Endpoint**: Converts the JSON into structured, analyzable data.")

with col2:
    st.markdown("<div class='soft-subheader'>Our Goal</div>", unsafe_allow_html=True)
    st.write("""
We focus on fraud-related document analysis using OCR and Gemini to clean,
structure, and visualize FBI fraud reports. Our goal is to help identify trends,
common scams, and fraud patterns affecting consumers 60+.
""")
    

# ------- IMAGE LEFT — TEXT RIGHT -------
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("<div class='soft-subheader'>Project Summary</div>", unsafe_allow_html=True)   
    st.write("""
    We studied data published by the Federal Bureau of Investigation (FBI) in their Annual Internet Crime Reports. These PDF's contain much valuable information, but we came across issues properly webscraping data formatted in charts. This led us to search for a solution.
 
    Deepseek recently released their Optical Character Recognition (OCR) model that specicalizes in shrinking the amount of vision tokens required per PDF page, effectivly lowering the cost of runs while maintaining accuracy. To work around the capacities of a typical computer GPU, we connected this model to Modal's CPU to create a functioning API that collects all text data from PDF's as Markdown in a JSON file. 
              """)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.image("imagesForSL/FBI-Logo.jpg", width=550)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("""
   These JSON files are fed into our Gemini endpoint and converted into a useable format and imported to Supabase. The newly processed data can now be called to create visulizations displaying your findings.

**Note**: While we have created a full pipline for PDF's to be scraped, processed, and formatted in one run, we cannot demonstrate due to the high cost from utilizing Modal's platform.
""")

st.markdown("""
    <div class="flowchart">
        <span style="padding:8px 12px; background:#C8DAB9; border-radius:6px;">PDF</span>
        ➜
        <span style="padding:8px 12px; background:#C8DAB9; border-radius:6px;">OCR (Modal)</span>
        ➜
        <span style="padding:8px 12px; background:#C8DAB9; border-radius:6px;">Gemini Analysis</span>
        ➜
        <span style="padding:8px 12px; background:#C8DAB9; border-radius:6px;">DataFrame</span>
        ➜
        <span style="padding:8px 12px; background:#C8DAB9; border-radius:6px;">Supabase</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""

""")

# GitHub button
st.markdown("""
    <a href="https://github.com/kleedom19/FBI-Fraud" target="_blank" class="sage-button">
        Visit Our GitHub!
    </a>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
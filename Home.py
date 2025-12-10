import streamlit as st
import logging
import sys

# -------------------------
# Setup logging
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logging.info("Starting Home.py Streamlit app...")

# -------------------------
# Page configuration
# -------------------------
st.set_page_config(layout="wide", page_title="Homepage", page_icon="📊")
logging.info("Streamlit page config set")

# --- TOP BANNER ---
try:
    st.markdown("""
        <style>
            .top-banner { width: 100%; background-color: #C8DAB9; padding: 25px 0; text-align: center; font-size: 26px; font-weight: bold; color: black; border-radius: 6px; margin-bottom: 25px; }
            .soft-subheader { background-color: #E6F0D9; padding: 10px 14px; border-radius: 6px; font-size: 20px; font-weight: 600; margin-bottom: 10px; }
            .sage-button { display: inline-block; padding: 10px 20px; background-color: #C8DAB9; color: black; font-size: 16px; text-decoration: none; border-radius: 8px; border: none; }
            .flowchart { background-color:#E6F0D9; padding:20px; border-radius:10px; text-align:center; font-size:18px; font-weight:600; }
            .sage-button:hover { background-color: #B7CBA7; }
            .thin-line { border: 0.5px solid #cccccc; margin: 10px 0; }
            .sage-box { background-color: #E6F0D9; padding: 20px; border-radius: 10px; margin-bottom: 25px; }
            .sage-header { background-color: #C8DAB9; padding: 10px 14px; border-radius: 6px; font-size: 20px; font-weight: 600; margin-bottom: 14px; display: inline-block; }
            .sage-image { border-radius: 10px; border: 3px solid #C8DAB9; }
        </style>
        <div class="top-banner">Fraud Document Reader</div>
    """, unsafe_allow_html=True)
    logging.info("Top banner loaded")
except Exception as e:
    logging.error(f"Failed to load top banner: {e}")

# --- AUTHOR TEXT ---
try:
    st.write("""
    **Authors**: Katie Leedom, Jacob German, Rohan Salwekar, Christian Ohlsson

    This app introduces our project which aims to build a simple OCR to Gemini pipeline that helps scrape and structure fraud data stored in charts within PDFs for further analysis.
    """)
    logging.info("Author text displayed")
except Exception as e:
    logging.error(f"Failed to display author text: {e}")

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)

# --- TWO COLUMNS ---
try:
    col1, col2 = st.columns(2)
    logging.info("Columns created")
except Exception as e:
    logging.error(f"Failed to create columns: {e}")

# Column 1 content
with col1:
    try:
        st.markdown("<div class='soft-subheader'>Key Features</div>", unsafe_allow_html=True)
        st.write("- **OCR**: Deepseek's OCR was used to extract chart-based data efficiently, outputting a JSON file.")
        st.write("- **Gemini Endpoint**: Converts the JSON into structured, analyzable data.")
        logging.info("Column 1: Key Features displayed")
    except Exception as e:
        logging.error(f"Column 1 failed: {e}")

    try:
        st.markdown("<div class='soft-subheader'>Project Summary</div>", unsafe_allow_html=True)
        st.write("""
        We studied data published by the Federal Bureau of Investigation (FBI) in their Annual Internet Crime Reports. These PDFs contain much valuable information, but we came across issues properly webscraping data formatted in charts. This led us to search for a solution. Deepseek recently released their Optical Character Recognition (OCR) model that specializes in shrinking the amount of vision tokens required per PDF page, effectively lowering the cost of runs while maintaining accuracy.
        """)
        logging.info("Column 1: Project Summary displayed")
    except Exception as e:
        logging.error(f"Column 1 project summary failed: {e}")

# Column 2 content
with col2:
    try:
        st.markdown("<div class='soft-subheader'>Business Solution</div>", unsafe_allow_html=True)
        st.write("""
        While we explored FBI documents, we discovered the financial data documents were mostly charts in PDFs, which are known for being more difficult to scrape. After further research, it was discovered that banking documents, such as financial reports, are typically published in this format. 

        Our team set out to create a tool to aid in the scraping process of these documents.
        """)
        logging.info("Column 2: Business Solution displayed")
    except Exception as e:
        logging.error(f"Column 2 business solution failed: {e}")

    try:
        st.markdown("<div class='soft-subheader'>Our Goal</div>", unsafe_allow_html=True)
        st.write("""
        We focus on fraud-related document analysis using OCR and Gemini to clean,
        structure, and visualize FBI fraud reports. Our goal is to efficiently extract data stored in PDFs to help identify trends,
        common scams, and fraud patterns affecting consumers.
        """)
        logging.info("Column 2: Our Goal displayed")
    except Exception as e:
        logging.error(f"Column 2 goal failed: {e}")

# -------------------------
# Additional sections with logging
# -------------------------
try:
    st.write("""
    To work around the capacities of a typical computer GPU, we connected this model to Modal's CPU to create a functioning API that collects all text data from PDFs as Markdown in a JSON file. These JSON files are fed into our Gemini endpoint and converted into a useable format and imported to Supabase. The newly processed data can now be called to create visualizations displaying your findings.

    **Note**: While we have created a full pipeline for PDFs to be scraped, processed, and formatted in one run, we cannot demonstrate due to the high cost from utilizing Modal's platform.
    """)
    logging.info("Explanation of pipeline displayed")
except Exception as e:
    logging.error(f"Pipeline explanation failed: {e}")

# Flowchart
try:
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
    logging.info("Flowchart displayed")
except Exception as e:
    logging.error(f"Flowchart failed: {e}")

# GitHub button
try:
    st.markdown("""
        <a href="https://github.com/kleedom19/FBI-Fraud" target="_blank" class="sage-button">
            Visit Our GitHub!
        </a>
    """, unsafe_allow_html=True)
    logging.info("GitHub button displayed")
except Exception as e:
    logging.error(f"GitHub button failed: {e}")

logging.info("Home.py Streamlit app finished loading")

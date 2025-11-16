import streamlit as st

st.set_page_config(page_title="DTSC 3602 Final Project")

st.title("DTSC 3602 Final Project: Fraud Detection for Consumers 60+")
st.write("""
This app introduces our final project for DTSC 3602. Our goal is to build a simple AI/ML pipeline that helps analyze fraud cases affecting adults 60 and older using public FBI data. We're focusing on document analysis, OCR, and structured data removal from the FBI's reports and scam summaries. This helps us identify common scams, track which states see the most activity, and understand how fraud against older consumers change over time. The goal is to make the information easier to read, analyze, and use for future prevention efforts. 

**Findings for 60+ consumers**
- Top states where fraud occurs 
- Common types of scams targeting older adults
- Trends over time
""")

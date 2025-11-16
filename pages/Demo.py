import streamlit as st 

st.title("API Demo & Workflow")

st.write("""
This page shows how our OCR + AI workflow works:
1. Convert PDFs into PNG images
2. Run Deepseek OCR to extract text 
3. Turn OCR results into Markdown
4. Use Gemini to convert markdown into a pandas DataFrame

Below are screenshots and examples of each step:
""")
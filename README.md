# FBI-Fraud
### Making messy FBI fraud PDFs easy to read and use for spotting scams

## Team Members 
- Katie Leedom
- Rohan Salwekar
- Jacob German
- Christian Ohlsson

## Project Summary 
FBI-Fraud takes messy FBI fraud PDFs, extracts and organizes the data, and helps identify trends and common scams. It's especially useful for spotting frauds that target older adults over 60, making it easier to get clear insights from complex reports. 

## Features

- **Simple OCR Pipeline**: Extracts chart-based information from fraud PDFs using Deepseek OCR 
- **Gemini API Integration**: Converts messy PDF text/JSON into clean, strucutred tables
- **PDF Analysis**: Automates scraping, cleaning, and organizing fraud data
- **Jupyter Notebooks**: Interactive analysis and prototyping
- **Designed for Fraud Insights**: Helps highlight scams affecting vulnerable age groups 60+

## Quick Start 

Follow these steps to get FBI-Fraud running on your machine. Make sure you have **Python 3.9 or higher** installed. 

**Install uv** 
```bash 
# macOS / Linux 
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (Powershell) 
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip 
pip install uv
```
#Clone project
```bash
git clone https://github.com/kleedom19/FBI-Fraud
cd FBI-Fraud 
```
#Install dependencies
```bash
uv sync 
```
#Set up Environment variables
```bash
cp .env.example .env 
```
#Run a test OCR script 
```bash
uv run python deepseekOcr.py
```

## Project Structure 

Here's an overview of the main files and folders in FBI-Fraud

```
FBI-Fraud/
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── pyproject.toml           # Project configuration and dependencies
├── uv.lock                  # Locked dependency versions
├── requirements.txt         # Legacy requirements (for reference)
├── README.md               # This file
├── gemini_test.ipynb       # Gemini API testing notebook
├── deepseekOcr.py          # OCR processing script
└── pdfScraping.py          # PDF analysis script
```


## Visuals / Application Design 

FBI-Fraud processes messy FBI fraud PDF into clean, structured data that can be analyzed for fraud trends. This pipeline consists of four main stages: 

1. **Input PDFs** - Raw FBI fraud reports
2. **OCR Extraction** - `deepseekOcr.py` reads PDFs and extracts text/tables
3. **Data Cleaning / Structuring** - `gemini_test.ipynb` converts messy OCR output into structured JSON/tables.
4. **Analysis & Insights** - Jupyter notebook or Python scripts analyze the data and generate visualizations of trends affecting 60+ individuals


## Pipeline Diagram 

```
┌─────────────────┐
│   PDF File      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Modal + OCR    │─────▶│  OCR JSON Output │
│  (Expensive)     │      └────────┬───────────┘
└─────────────────┘              │
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Check Supabase  │
                         │     Cache        │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
            ┌──────────────┐          ┌──────────────────┐
            │   Cached?    │          │  Gemini Analysis │
            │   Return     │          │  (Standalone)    │
            └──────────────┘          └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │  Pandas DataFrame│
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │  Save to Supabase│
                                      └──────────────────┘
```


## Clear Findings 

FBI-Fraud extracts and organizes messy FBI fraud PDFs to highlight trends and common sense, especially targeting individuals 60+. By combining OCR with the Gemini API, we can clean text, structure data, and generate insights automatically. 

### Key Findings 
Here is an example showing how raw OCR text from a pdf is transformed into a structured table:

```python
from deepseekOcr import model, tokenizer
import pandas as pd 

# Raw text example from page28.pdf
raw_text = """ 
Crime Type, Count
Phishing/Spoofing, 23252
Advanced Fee, 1897
Tech Support, 16777
Real Estate, 1765
Extortion, 12618
""" 

# Convert raw text into structured DataFrame
data_lines = [line.split(",") for line in raw_text.strip().split("\n")[1:]]
df = pd.DataFrame(data_lines, columns=["Crime Type", "Count"])
df["Count"] = df["Count"].astype(int)

# Display cleaned DataFrame
print(df.head())
```

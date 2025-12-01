# FBI-Fraud
### Making messy FBI fraud PDFs easy to read and use for spotting scams

## Team Members 
- Katie Leedom
- Rohan Salwekar
- Jacob German
- Christian Ohllson

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
## Code Snippets 

### 1. Sample Input PDF 
Here is an example snippet from `page28.pdf` showing crime types reported by individuals 60+:

| Crime Type           | Count  | Crime Type                      | Count |
| -------------------- | ------ | ------------------------------- | ----- |
| Phishing/Spoofing    | 23,252 | Advanced Fee                    | 1,897 |
| Tech Support         | 16,777 | Real Estate                     | 1,765 |
| Extortion            | 12,618 | Lottery/Sweepstakes/Inheritance | 1,711 |
| Personal Data Breach | 9,827  | Harassment/Stalking             | 696   |

### 2. OCR Output 
After running `deepseekOcr.py`, the OCR produces raw text

```json
{
  "filename": "page28.pdf",
  "total_pages": 1,
  "results": [
    {
      "page": 1,
      "text": "<table><tr><td>Phishing/Spoofing</td><td>23,252</td><td>Advanced Fee</td><td>1,897</td></tr>...</table>",
      "status": "success"
    }
  ]
}
```

### 3. Cleaned Data Snippet 

| Crime Type                      | Count  |
| ------------------------------- | ------ |
| Phishing/Spoofing               | 23,252 |
| Tech Support                    | 16,777 |
| Extortion                       | 12,618 |
| Personal Data Breach            | 9,827  |
| Advanced Fee                    | 1,897  |
| Real Estate                     | 1,765  |
| Lottery/Sweepstakes/Inheritance | 1,711  |
| Harassment/Stalking             | 696    |

## Visuals / Application Design 

FBI-Fraud processes messy FBI fraud PDF into clean, structured data that can be analyzed for fraud trends. This pipeline consists of four main stages: 

1. **Input PDFs** - Raw FBI fraud reports
2. **OCR Extraction** - `deepseekOcr.py` reads PDFs and extracts text/tables
3. **Data Cleaning / Structuring** - `gemini_test.ipynb` converts messy OCR output into structured JSON/tables.
4. **Analysis & Insights** - Jupyter notebook or Python scripts analyze the data and generate visualizations of trends affecting 60+ individuals

### Pipeline Diagram

flowchart LR
    A[Raw FBI Fraud PDFs] --> B[OCR Extraction<br/>deepseekOcr.py]
    B --> C[Gemini Cleaning<br/>Structured JSON/Tables]
    C --> D[Analysis & Visualization<br/>Jupyter / Python]
    D --> E[Insights<br/>Fraud Trends for Age 60+]

## Clear Findings

FBI-Fraud extracts and organizes messy FBI fraud PDFs to highlight trends and common scams, especially targeting individuals 60+. By combining OCR with the Gemini API, we can clean text, structure data, and generate insights automatically.

### Key Findings

| Crime Type                      | Count  |
| ------------------------------- | ------ |
| Phishing/Spoofing               | 23,252 |
| Tech Support                    | 16,777 |
| Extortion                       | 12,618 |
| Personal Data Breach            | 9,827  |
| Advanced Fee                    | 1,897  |
| Real Estate                     | 1,765  |
| Lottery/Sweepstakes/Inheritance | 1,711 |
| Harassment/Stalking             | 696    |

**Insights:**  

- **Phishing/Spoofing is the most common scam** targeting older adults.  
- **Tech support and extortion scams** also impact thousands of victims.  
- Data-driven analysis helps quickly **identify patterns across large PDF datasets**, which was previously difficult due to messy formatting.

### Gemini API Example

Using the Gemini API, messy text can be summarized or transformed into insights:

```python
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found! Please set it in your .env file:\n"
        "GEMINI_API_KEY=your_key_here"
    )
genai.configure(api_key=api_key)

# Generate test response
model = genai.GenerativeModel("gemini-2.0-flash-lite-001")
response = model.generate_content("Explain how AI works in a few words")
print(response.text)


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

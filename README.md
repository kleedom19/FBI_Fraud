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

### Code Snippet / Key Findings

#### 1. Sample input PDF
Here is an example snippet from 'page28.pdf' showing crime types reported by individuals 60+ and also including a screenshot of the table:

| Crime Type                         | Count  |
|-----------------------------------|--------|
| Phishing/Spoofing                  | 23,252 |
| Tech Support                        | 16,777 |
| Extortion                           | 12,618 |
| Personal Data Breach                | 9,827  |
| Advanced Fee                        | 1,897  |
| Real Estate                         | 1,765  |
| Lottery/Sweepstakes/Inheritance    | 1,711  |
| Harassment/Stalking                 | 696    |

<img width="568" height="230" alt="step1" src="https://github.com/user-attachments/assets/64e3057c-a8d8-43d4-a40e-455eebabf4db" />


#### OCR Output 
After running 'deepseekOcr.py', the OCR produces raw JSON text: 

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
  }
}
```
#### Key Findings (Financial Losses by Age Group) 
This chart shows the financial losses from fraud are distributed across different age groups. 

- Adults over 60 suffer the highest total losses, which exceeds $1.5 billion.
- Ages 50-59 and 40-49 also experience significant losses, with total losses of $1 billion.
- Those younger age groups lose less, showing a huge drop in total financial loss.
- This pattern shows that older adults are more targeted by high-dollar scams.

<img width="700" height="625" alt="step4" src="https://github.com/user-attachments/assets/a4825e0f-08ab-448c-ac5d-9c482035cf27" />

## Importance 

In conclusion, our project makes it easier to work with messy FBI fraud PDF’s which are full of charts and hard to scrape. Using OCR and Gemini API, our tool cleans up the data, organizes it, and turns it into clear tables and visuals. This way, we can spot trends, common scams, and patterns in fraud. Overall, our project is a way to turn complicated reports into useful insights for understanding and preventing fraud. 

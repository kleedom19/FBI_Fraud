# FBI-Fraud OCR Pipeline

**Separated Architecture**: Modal/OCR and Gemini/Supabase are completely independent.

- **Modal + DeepSeek OCR**: Expensive, runs OCR on PDFs
- **Gemini + Supabase**: Cheap, analyzes OCR output and stores results (works standalone, no Modal required!)

## Architecture

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

## Quick Start

### 1. Install Dependencies

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
cd FBI-Fraud
uv sync
```

### 2. Environment Setup

Create a `.env` file with your credentials:

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
# For Modal (bypasses RLS): Use service role key instead
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

### 3. Set Up Modal Secrets (For OCR Only)

```bash
# Set Modal authentication
export MODAL_TOKEN_ID="your_token_id"
export MODAL_TOKEN_SECRET="your_token_secret"

# Create secrets in Modal
modal secret create deepseek-secrets \
  TOKEN_ID="your_token_id" \
  TOKEN_SECRET="your_token_secret"

modal secret create gemini-supabase-secrets \
  GEMINI_API_KEY="your_gemini_api_key" \
  SUPABASE_URL="https://your-project.supabase.co" \
  SUPABASE_SERVICE_KEY="your_supabase_service_role_key"
```

### 4. Create Supabase Table

Run this SQL in your Supabase SQL Editor:

```sql
CREATE TABLE ocr_results (
  id BIGSERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  formatted_json TEXT NOT NULL,
  original_ocr_data JSONB,
  ocr_raw_data JSONB,  -- Raw OCR for caching
  dataframe_json JSONB,  -- Pandas DataFrame as JSON
  keywords TEXT[],  -- Extracted keywords
  key_metrics JSONB,  -- Document metadata
  total_pages INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disable RLS if using service role key
ALTER TABLE ocr_results DISABLE ROW LEVEL SECURITY;
```

## Usage

### Option 1: Complete Pipeline (Recommended)

Use `client_pipeline.py` to orchestrate everything:

```bash
# Full pipeline: Check cache → OCR (if needed) → Analyze → Save
python client_pipeline.py path/to/file.pdf

# Skip OCR, analyze existing OCR data from Supabase
python client_pipeline.py path/to/file.pdf --skip-ocr

# Only run OCR, skip analysis
python client_pipeline.py path/to/file.pdf --skip-analysis
```

**What it does:**
1. ✅ Checks Supabase cache (avoids expensive OCR if already done)
2. 📤 Runs OCR on Modal (only if not cached)
3. 🤖 Analyzes with Gemini (standalone, no Modal)
4. 📊 Converts to DataFrame
5. 💾 Saves to Supabase

### Option 2: Run OCR Only (Modal)

```bash
# Deploy to Modal
modal deploy deploy_modal.py

# Test OCR endpoint
python test_api.py path/to/file.pdf

# This saves OCR results to: filename_ocr.json
```

### Option 3: Analyze OCR Output (Standalone - No Modal!)

```bash
# Analyze OCR JSON file with Gemini
python analyze_ocr.py filename_ocr.json

# Analyze OCR data from Supabase cache
python analyze_ocr.py --from-supabase filename.pdf

# Check if analysis exists in cache
python analyze_ocr.py --check-cache filename.pdf
```

**This works completely independently of Modal!** No Modal deployment needed.

### Option 4: Standalone Analysis Server

Run a FastAPI server for analysis (no Modal):

```bash
# Start server
uvicorn analyze_server:app --port 8001

# Or
python analyze_server.py
```

Then use the API:
```bash
# Check cache
curl "http://localhost:8001/check-cache?filename=document.pdf"

# Analyze OCR JSON
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d @ocr_results.json
```

## Workflow Examples

### Example 1: First Time Processing

```bash
# Step 1: Run OCR (expensive, costs money)
python test_api.py document.pdf
# Output: document_ocr.json

# Step 2: Analyze with Gemini (cheap, standalone)
python analyze_ocr.py document_ocr.json
# Saves to Supabase with DataFrame
```

### Example 2: Re-analyze Existing OCR

```bash
# If you already have OCR results, just analyze
python analyze_ocr.py document_ocr.json

# Or if OCR is cached in Supabase
python analyze_ocr.py --from-supabase document.pdf
```

### Example 3: Avoid Duplicate OCR

```bash
# Use client_pipeline - it checks cache automatically
python client_pipeline.py document.pdf
# If cached, skips OCR and returns cached analysis
```

## Key Features

### ✅ Cost Optimization
- **Caching**: Avoid duplicate OCR runs (expensive)
- **Separation**: Run Gemini/Supabase without Modal (cheap)
- **Re-analysis**: Analyze same OCR multiple times without re-running OCR

### ✅ Standalone Analysis
- Gemini and Supabase work **completely independently** of Modal
- No Modal deployment needed for analysis
- Can run analysis on any OCR JSON file

### ✅ DataFrame Conversion
- Automatically converts Gemini analysis to pandas DataFrame
- Stores structured data in Supabase
- Easy to query and analyze later

## Project Structure

```
FBI-Fraud/
├── deploy_modal.py          # Modal deployment (OCR only)
├── ocr_endpoint.py          # FastAPI endpoints (OCR + analyze)
├── deepseekOcr.py           # DeepSeek OCR model loader
├── gemini_supabase.py       # Shared Gemini/Supabase functions ⭐
├── analyze_ocr.py           # Standalone Gemini/Supabase script ⭐
├── analyze_server.py        # Standalone FastAPI server ⭐
├── client_pipeline.py       # Complete pipeline orchestrator ⭐
├── test_api.py              # Test OCR endpoint only
├── verify_supabase.py       # Verify what's saved in Supabase
├── sample_ocr_data.json     # Sample data for testing
├── README.md                # Main documentation
├── QUICK_START.md           # Quick start guide
├── TESTING.md               # Testing guide
└── pyproject.toml           # Dependencies
```

## API Endpoints

### Modal OCR Endpoint (Expensive)
- `POST /ocr/pdf` - Run OCR on PDF

### Analysis Endpoints (Standalone - No Modal)
- `GET /check-cache?filename=...` - Check if cached
- `POST /analyze` - Analyze OCR JSON with Gemini

## Troubleshooting

### Supabase Connection Errors
- **"Name or service not known"**: Check `SUPABASE_URL` format (must be `https://your-project.supabase.co`, no trailing slash)
- **"Table does not exist"**: Create the `ocr_results` table (see SQL above)
- **"row-level security policy" (42501)**: Use `SUPABASE_SERVICE_KEY` instead of `SUPABASE_KEY`

### Gemini Errors
- **429 Rate Limit**: Automatic retry with exponential backoff (2s, 4s, 8s)
- Falls back to structured format if analysis fails

### Modal Errors
- **Secret not found**: Create secrets using commands above
- **Deployment fails**: Check Modal authentication

## Dependencies

- `google-generativeai`: Gemini API
- `supabase`: Supabase client
- `python-dotenv`: Environment variables
- `pandas`: DataFrame conversion
- `fastapi`, `uvicorn`: API framework
- `transformers`, `torch`: OCR model (Modal only)

## Cost Optimization Tips

1. **Always check cache first** - Use `client_pipeline.py` or `analyze_ocr.py --check-cache`
2. **Save OCR results** - Keep `*_ocr.json` files for re-analysis
3. **Run analysis separately** - Use `analyze_ocr.py` without Modal
4. **Use Supabase cache** - Store OCR results to avoid re-running expensive OCR

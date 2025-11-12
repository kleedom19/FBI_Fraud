# FBI-Fraud OCR Pipeline

OCR pipeline using DeepSeek OCR → Gemini formatting → Supabase storage, deployed on Modal.

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
```

### 3. Set Up Modal Secrets

```bash
# Set Modal authentication
export MODAL_TOKEN_ID="ak-AAaiieeJF2MoBeNbzdNGf9"
export MODAL_TOKEN_SECRET="as-9juuxWSvAbsYs1JD4lmqKA"

# Create secrets in Modal
modal secret create deepseek-secrets \
  TOKEN_ID="your_token_id" \
  TOKEN_SECRET="your_token_secret"

modal secret create gemini-supabase-secrets \
  GEMINI_API_KEY="your_gemini_api_key" \
  SUPABASE_URL="https://your-project.supabase.co" \
  SUPABASE_KEY="your_supabase_key"
```

### 4. Create Supabase Table

Run this SQL in your Supabase SQL Editor:

```sql
CREATE TABLE ocr_results (
  id BIGSERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  formatted_json TEXT NOT NULL,
  original_ocr_data JSONB,
  total_pages INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Running the Pipeline

### Option 1: Test Gemini & Supabase Only (No Cost)

Test the integration without running expensive OCR:

```bash
# Use default sample data
uv run python test_gemini_supabase.py

# Use custom JSON file
uv run python test_gemini_supabase.py --sample-json sample_ocr_data.json

# Skip Gemini or Supabase if needed
uv run python test_gemini_supabase.py --skip-gemini
uv run python test_gemini_supabase.py --skip-supabase
```

### Option 2: Full Modal Pipeline (Costs Money)

1. **Deploy to Modal:**
   ```bash
   modal deploy deploy_modal.py
   ```

2. **Test with PDF:**
   ```bash
   # Update BASE_URL in test_api.py with your Modal endpoint
   uv run python test_api.py path/to/your/file.pdf
   ```

   Or use curl:
   ```bash
   curl -X POST "https://your-workspace--deepseek-ocr-serve.modal.run/ocr/pdf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
   ```

## Pipeline Flow

1. **PDF Upload** → DeepSeek OCR extracts text from each page
2. **Gemini Formatting** → Raw OCR JSON is cleaned and structured
3. **Supabase Storage** → Formatted JSON saved to `ocr_results` table
4. **Response** → Returns original OCR + formatted JSON + save status

## Troubleshooting

### Supabase Connection Errors

- **"Name or service not known"**: Check `SUPABASE_URL` format (must be `https://your-project.supabase.co`, no trailing slash)
- **"Table does not exist"**: Create the `ocr_results` table in Supabase
- **"Invalid SUPABASE_URL format"**: Ensure URL starts with `https://` and contains `.supabase.co`

### Gemini Errors

- **429 Rate Limit**: Wait and retry, or check your API quota
- Falls back to original JSON if formatting fails

### Modal Errors

- **Secret not found**: Create secrets using commands above
- **Deployment fails**: Check Modal authentication and secrets

## Project Structure

```
FBI-Fraud/
├── deploy_modal.py          # Modal deployment configuration
├── ocr_endpoint.py          # FastAPI endpoint (OCR + Gemini + Supabase)
├── deepseekOcr.py           # DeepSeek OCR model loader
├── test_api.py              # Test full Modal pipeline
├── test_gemini_supabase.py  # Test Gemini/Supabase only (no cost)
├── sample_ocr_data.json     # Sample data for testing
└── pyproject.toml           # Dependencies
```

## Dependencies

- `google-generativeai`: Gemini API
- `supabase`: Supabase client
- `python-dotenv`: Environment variables
- `fastapi`, `uvicorn`: API framework
- `transformers`, `torch`: OCR model

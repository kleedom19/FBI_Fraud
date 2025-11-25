# Testing Guide

## Quick Start Testing (Cheapest - No Modal Required!)

### Step 1: Test Gemini + Supabase Only (FREE/Cheap)

This tests the analysis pipeline without running expensive OCR:

```bash
# Make sure you're in the project directory
cd "/Users/rohansalwekar/Coding/dtsc 3601 & 3602/FBI-Fraud"

# Test with sample data (no Modal, no OCR costs)
uv run python analyze_ocr.py sample_ocr_data.json
```

**Expected output:**
- ✅ Loads sample OCR data
- ✅ Analyzes with Gemini
- ✅ Converts to DataFrame
- ✅ Saves to Supabase

**If you see errors:**
- Check your `.env` file has `GEMINI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY`
- Make sure Supabase table exists (see README)

---

## Full Pipeline Testing

### Step 2: Test Complete Pipeline (Includes Modal OCR - Costs Money!)

```bash
# Option A: Use existing PDF file
uv run python client_pipeline.py page28.pdf

# Option B: Use your own PDF
uv run python client_pipeline.py path/to/your/file.pdf
```

**What happens:**
1. Checks Supabase cache (if already analyzed, returns cached result)
2. If not cached: Runs OCR on Modal (💰 costs money)
3. Analyzes OCR with Gemini (standalone, cheap)
4. Saves to Supabase

---

## Step-by-Step Testing

### Test 1: Check Cache (No Cost)

```bash
# Check if a file is already cached
uv run python analyze_ocr.py --check-cache page28.pdf
```

### Test 1b: Delete Cache (No Cost)

```bash
# Delete cached analysis for a file
uv run python analyze_ocr.py --delete-cache page28.pdf
```

### Test 2: Analyze Existing OCR JSON (No Modal Cost)

If you already have OCR results:

```bash
# Analyze a saved OCR JSON file
uv run python analyze_ocr.py ocr_results.json

# Or analyze from Supabase cache
uv run python analyze_ocr.py --from-supabase page28.pdf
```

### Test 3: Run OCR Only (Modal - Costs Money)

```bash
# First, deploy to Modal
modal deploy deploy_modal.py

# Then test OCR endpoint
uv run python test_api.py page28.pdf
```

This will:
- Run OCR on Modal
- Save results to `page28_ocr.json`
- **NOT** run Gemini/Supabase (that's separate)

### Test 4: Full Pipeline (Modal + Gemini + Supabase)

```bash
# This does everything: OCR → Analyze → Save
uv run python client_pipeline.py page28.pdf
```

---

## Standalone Analysis Server

Test the analysis API server (no Modal):

```bash
# Start the server
uv run python analyze_server.py
# Or: uvicorn analyze_server:app --port 8001

# In another terminal, test it:
curl "http://localhost:8001/check-cache?filename=page28.pdf"

# Or analyze OCR JSON:
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d @sample_ocr_data.json
```

---

## Troubleshooting

### "GEMINI_API_KEY not found"
- Check your `.env` file exists
- Make sure it has: `GEMINI_API_KEY=your_key_here`

### "SUPABASE_URL not found"
- Add to `.env`: `SUPABASE_URL=https://your-project.supabase.co`
- Add: `SUPABASE_KEY=your_key_here`

### "Table does not exist"
- Run the SQL from README to create the `ocr_results` table in Supabase

### "Modal endpoint not found"
- Deploy first: `modal deploy deploy_modal.py`
- Update `client_pipeline.py` or `test_api.py` with your Modal endpoint URL

---

## Recommended Testing Order

1. ✅ **First**: Test Gemini/Supabase only (cheapest)
   ```bash
   uv run python analyze_ocr.py sample_ocr_data.json
   ```

2. ✅ **Second**: Test full pipeline with a small PDF
   ```bash
   uv run python client_pipeline.py page28.pdf
   ```

3. ✅ **Third**: Test OCR endpoint separately
   ```bash
   modal deploy deploy_modal.py
   uv run python test_api.py page28.pdf
   ```


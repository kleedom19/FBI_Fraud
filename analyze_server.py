#!/usr/bin/env python3
"""
Standalone FastAPI server for Gemini analysis and Supabase storage.
Runs completely independently of Modal - no Modal required!

Usage:
    uvicorn analyze_server:app --host 0.0.0.0 --port 8001
    # Or
    python -m uvicorn analyze_server:app --port 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from gemini_supabase import (
    check_cache,
    get_ocr_from_supabase,
    format_with_gemini,
    convert_to_dataframe,
    save_to_supabase
)

app = FastAPI(
    title="OCR Analysis API",
    description="Gemini analysis and Supabase storage (standalone - no Modal required)",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "OCR Analysis API (Gemini + Supabase)",
        "modal_required": False
    }

@app.get("/check-cache")
async def check_cache_endpoint(filename: str):
    """Check if analysis exists in Supabase cache."""
    result = check_cache(filename)
    return result

@app.post("/analyze")
async def analyze_ocr_endpoint(ocr_data: dict):
    """
    Analyze OCR output using Gemini and save to Supabase.
    Works standalone - no Modal required!
    
    Expected input:
    {
        "filename": "document.pdf",
        "total_pages": 2,
        "results": [
            {"page": 1, "text": "...", "status": "success"},
            ...
        ]
    }
    """
    try:
        # Validate input
        if "filename" not in ocr_data or "results" not in ocr_data:
            raise HTTPException(status_code=400, detail="Missing 'filename' or 'results' in input")
        
        filename = ocr_data['filename']
        
        # Check cache first
        print(f"Checking cache for {filename}...")
        cache_result = check_cache(filename)
        if cache_result.get("cached"):
            print("Found cached data, returning...")
            return {
                "status": "cached",
                "message": "Using cached analysis",
                "data": cache_result["data"]
            }
        
        # Analyze with Gemini
        print("Analyzing OCR output with Gemini...")
        formatted_json = format_with_gemini(ocr_data)
        print("Gemini analysis completed")
        
        # Parse Gemini output
        gemini_analysis = json.loads(formatted_json)
        
        # Convert to DataFrame
        print("Converting to DataFrame...")
        dataframe_data = convert_to_dataframe(gemini_analysis)
        print("DataFrame conversion completed")
        
        # Save to Supabase
        print("Saving to Supabase...")
        supabase_result = save_to_supabase(
            filename, 
            formatted_json, 
            ocr_data,
            dataframe_data
        )
        
        if supabase_result.get("success"):
            return {
                "status": "success",
                "filename": filename,
                "gemini_analysis": gemini_analysis,
                "dataframe": dataframe_data,
                "supabase_saved": True
            }
        else:
            return {
                "status": "partial_success",
                "filename": filename,
                "gemini_analysis": gemini_analysis,
                "dataframe": dataframe_data,
                "supabase_saved": False,
                "supabase_error": supabase_result.get("error")
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from PIL import Image 
import os
from pathlib import Path
import tempfile
import json
from gemini_supabase import (
    get_gemini_model,
    get_supabase_client,
    format_with_gemini,
    convert_to_dataframe,
    save_to_supabase,
    check_cache
)

app = FastAPI(
    title="DeepSeek OCR API",
    description="OCR API for PDF documents using DeepSeek-OCR",
    version="1.0.0"
)

# Lazy load model only when needed
_model = None
_tokenizer = None

def get_model():
    """Lazy load the model to avoid loading it at import time."""
    global _model, _tokenizer
    if _model is None:
        from deepseekOcr import model, tokenizer
        _model = model
        _tokenizer = tokenizer
    return _model, _tokenizer

TOKEN_ID = os.getenv("TOKEN_ID")
TOKEN_SECRET = os.getenv("TOKEN_SECRET")

# All Gemini/Supabase functions are imported from gemini_supabase.py

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "DeepSeek OCR API",
        "authenticated": bool(TOKEN_ID and TOKEN_SECRET)
    }

@app.get("/health")
async def health():
    """Detailed health check."""
    model, tokenizer = get_model()
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "tokenizer_loaded": tokenizer is not None
    }

@app.post("/ocr/pdf")
async def ocr_pdf(file: UploadFile = File(...)):
    """
    Extract text from PDF using OCR.
    
    Args:
        file: PDF file to process
        
    Returns:
        JSON with OCR results for each page
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    model, tokenizer = get_model()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Convert PDF to images
            pdf_bytes = await file.read()
            images = convert_from_bytes(pdf_bytes)

            results = []
            for i, img in enumerate(images, start=1):
                try:
                    image_path = os.path.join(tmpdir, f"page_{i}.png")
                    img.save(image_path, "PNG")

                    prompt = "<image>\n<|grounding|>Convert the document to markdown. "
                    output_dir = os.path.join(tmpdir, f"page_{i}_output")

                    # Run OCR inference - capture the return value
                    print(f"Processing page {i}...")
                    ocr_result = model.infer(
                        tokenizer,
                        prompt=prompt,
                        image_file=image_path,
                        output_path=output_dir,
                        base_size=1024,
                        image_size=640,
                        crop_mode=True,
                        save_results=True,
                        test_compress=True
                    )
                    print(f"OCR inference completed for page {i}")
                    
                    # First, try to use the returned value if it exists
                    if ocr_result and isinstance(ocr_result, str) and ocr_result.strip():
                        print(f"Using OCR result from return value (length: {len(ocr_result)})")
                        results.append({
                            "page": i,
                            "text": ocr_result.strip(),
                            "status": "success"
                        })
                        continue

                    # If no return value, read from the output directory
                    print(f"Reading from output directory: {output_dir}")
                    output_path = Path(output_dir)
                    
                    # The model creates a directory with result files
                    if output_path.exists() and output_path.is_dir():
                        # DeepSeek-OCR typically creates files with specific names
                        # Look for any text-like files in the directory
                        all_files = list(output_path.rglob("*"))
                        
                        # Filter for actual files (not directories)
                        text_files = [f for f in all_files if f.is_file()]
                        
                        # Try to find the markdown/text content
                        markdown_content = None
                        
                        for file_path in text_files:
                            try:
                                # Read the file
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content = f.read().strip()
                                    
                                    # If content exists and looks like markdown/text, use it
                                    if content:
                                        markdown_content = content
                                        print(f"Found OCR output in: {file_path.name}")
                                        break
                            except Exception as e:
                                print(f"Could not read {file_path.name}: {e}")
                                continue
                        
                        if markdown_content:
                            results.append({
                                "page": i,
                                "text": markdown_content,
                                "status": "success"
                            })
                        else:
                            # Debug: show what files exist
                            file_list = [f.name for f in text_files[:10]]
                            results.append({
                                "page": i,
                                "text": "",
                                "status": "error",
                                "error": f"No readable content found. Files in directory: {file_list}"
                            })
                    elif output_path.exists() and output_path.is_file():
                        # If it's a single file, read it
                        with open(output_path, "r", encoding="utf-8") as f:
                            results.append({
                                "page": i,
                                "text": f.read(),
                                "status": "success"
                            })
                    else:
                        results.append({
                            "page": i,
                            "text": "",
                            "status": "error",
                            "error": f"Output path does not exist: {output_dir}"
                        })
                        
                except Exception as e:
                    results.append({
                        "page": i,
                        "text": "",
                        "status": "error",
                        "error": str(e)
                    })

            # Return OCR results only (no Gemini/Supabase - those are separate)
            return {
                "filename": file.filename,
                "total_pages": len(images),
                "results": results
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/check-cache")
async def check_cache_endpoint(filename: str):
    """Check if OCR results for a filename already exist in Supabase cache."""
    result = check_cache(filename)
    if result.get("cached"):
        return {
            "cached": True,
            "data": result["data"],
            "message": f"Found cached data for {filename}"
        }
    else:
        return {
            "cached": False,
            "data": None,
            "message": f"No cached data found for {filename}",
            "error": result.get("error")
        }

@app.post("/analyze")
async def analyze_ocr(ocr_data: dict):
    """
    Analyze OCR output using Gemini and save to Supabase.
    This endpoint works standalone - no Modal required.
    
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
        
        # Check cache first
        print(f"Checking cache for {ocr_data['filename']}...")
        cache_check = check_cache(ocr_data['filename'])
        if cache_check.get("cached"):
            print("Found cached data, returning...")
            return {
                "status": "cached",
                "message": "Using cached analysis",
                "data": cache_check["data"]
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
            ocr_data['filename'], 
            formatted_json, 
            ocr_data,
            dataframe_data
        )
        
        if supabase_result.get("success"):
            return {
                "status": "success",
                "filename": ocr_data['filename'],
                "gemini_analysis": gemini_analysis,
                "dataframe": dataframe_data,
                "supabase_saved": True
            }
        else:
            return {
                "status": "partial_success",
                "filename": ocr_data['filename'],
                "gemini_analysis": gemini_analysis,
                "dataframe": dataframe_data,
                "supabase_saved": False,
                "supabase_error": supabase_result.get("error")
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
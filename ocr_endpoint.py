from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from PIL import Image 
import os
from pathlib import Path
import tempfile
import json
import google.generativeai as genai
from supabase import create_client, Client
from datetime import datetime

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

# Initialize Gemini and Supabase clients
_gemini_model = None
_supabase_client = None

def get_gemini_model():
    """Lazy load Gemini model."""
    global _gemini_model
    if _gemini_model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite-001')
    return _gemini_model

def get_supabase_client():
    """Lazy load Supabase client with URL validation."""
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
        
        # Validate and clean URL
        supabase_url = supabase_url.strip()
        
        # Remove trailing slash if present
        if supabase_url.endswith('/'):
            supabase_url = supabase_url[:-1]
        
        # Validate URL format
        if not supabase_url.startswith('https://'):
            raise ValueError(
                f"Invalid SUPABASE_URL format: '{supabase_url}'. "
                "URL must start with 'https://' (e.g., 'https://your-project.supabase.co')"
            )
        
        if '.supabase.co' not in supabase_url:
            raise ValueError(
                f"Invalid SUPABASE_URL format: '{supabase_url}'. "
                "URL should be in format: 'https://your-project-id.supabase.co'"
            )
        
        # Validate key is not empty
        supabase_key = supabase_key.strip()
        if not supabase_key:
            raise ValueError("SUPABASE_KEY cannot be empty")
        
        try:
            _supabase_client = create_client(supabase_url, supabase_key)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create Supabase client. URL: '{supabase_url[:30]}...', Error: {str(e)}"
            )
    
    return _supabase_client

def format_with_gemini(ocr_json_data: dict) -> str:
    """
    Format OCR JSON output using Gemini.
    
    Args:
        ocr_json_data: Dictionary containing OCR results
        
    Returns:
        Formatted JSON string from Gemini
    """
    try:
        model = get_gemini_model()
        
        # Create a prompt for Gemini to format the OCR output
        prompt = f"""Please format and structure the following OCR output into a clean, well-organized JSON format.
        
The OCR output contains text extracted from a PDF document. Please:
1. Clean up any formatting issues
2. Structure the data logically
3. Preserve all important information
4. Return a valid JSON object

OCR Data:
{json.dumps(ocr_json_data, indent=2)}

Please return only the formatted JSON, no additional text or markdown formatting."""

        response = model.generate_content(prompt)
        formatted_output = response.text.strip()
        
        # Try to parse and validate JSON
        try:
            json.loads(formatted_output)
        except json.JSONDecodeError:
            # If Gemini didn't return pure JSON, try to extract it
            # Remove markdown code blocks if present
            if "```json" in formatted_output:
                formatted_output = formatted_output.split("```json")[1].split("```")[0].strip()
            elif "```" in formatted_output:
                formatted_output = formatted_output.split("```")[1].split("```")[0].strip()
            # Try parsing again
            json.loads(formatted_output)
        
        return formatted_output
    except Exception as e:
        print(f"⚠️ Error formatting with Gemini: {e}")
        # Return original JSON if Gemini fails
        return json.dumps(ocr_json_data, indent=2)

def save_to_supabase(filename: str, formatted_json: str, original_ocr_data: dict):
    """
    Save formatted OCR output to Supabase.
    
    Args:
        filename: Original PDF filename
        formatted_json: Gemini-formatted JSON string
        original_ocr_data: Original OCR results dictionary
        
    Returns:
        dict with 'success' bool and 'data' or 'error' message
    """
    try:
        supabase = get_supabase_client()
        
        # Prepare data for Supabase
        record = {
            "filename": filename,
            "formatted_json": formatted_json,
            "original_ocr_data": json.dumps(original_ocr_data),
            "created_at": datetime.utcnow().isoformat(),
            "total_pages": original_ocr_data.get("total_pages", 0)
        }
        
        # Insert into Supabase (assuming table name is "ocr_results")
        # You may need to adjust the table name based on your Supabase schema
        response = supabase.table("ocr_results").insert(record).execute()
        
        print(f"✅ Saved to Supabase: {response.data}")
        return {"success": True, "data": response.data}
    except ValueError as e:
        # URL validation errors
        error_msg = f"Supabase configuration error: {str(e)}"
        print(f"⚠️ {error_msg}")
        return {"success": False, "error": error_msg}
    except RuntimeError as e:
        # Client creation errors
        error_msg = f"Supabase connection error: {str(e)}"
        print(f"⚠️ {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        # Other errors (network, table not found, etc.)
        error_msg = str(e)
        print(f"⚠️ Error saving to Supabase: {error_msg}")
        # Provide helpful hints for common errors
        if "Name or service not known" in error_msg or "[Errno -2]" in error_msg:
            error_msg += " (Check SUPABASE_URL format: should be 'https://your-project.supabase.co')"
        elif "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            error_msg += " (Table 'ocr_results' may not exist. Create it in Supabase.)"
        return {"success": False, "error": error_msg}

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
                    print(f"🔍 Processing page {i}...")
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
                    print(f"✅ OCR inference completed for page {i}")
                    
                    # First, try to use the returned value if it exists
                    if ocr_result and isinstance(ocr_result, str) and ocr_result.strip():
                        print(f"📄 Using OCR result from return value (length: {len(ocr_result)})")
                        results.append({
                            "page": i,
                            "text": ocr_result.strip(),
                            "status": "success"
                        })
                        continue

                    # If no return value, read from the output directory
                    print(f"📁 Reading from output directory: {output_dir}")
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
                                        print(f"✅ Found OCR output in: {file_path.name}")
                                        break
                            except Exception as e:
                                print(f"⚠️ Could not read {file_path.name}: {e}")
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

            # Prepare OCR results
            ocr_data = {
                "filename": file.filename,
                "total_pages": len(images),
                "results": results
            }
            
            # Format with Gemini
            print("🤖 Formatting OCR output with Gemini...")
            formatted_json = format_with_gemini(ocr_data)
            print("✅ Gemini formatting completed")
            
            # Save to Supabase
            print("💾 Saving to Supabase...")
            supabase_result = save_to_supabase(file.filename, formatted_json, ocr_data)
            
            # Return response with both original and formatted data
            response_data = {
                "filename": file.filename,
                "total_pages": len(images),
                "results": results,
                "formatted_json": formatted_json,
                "supabase_saved": supabase_result.get("success", False) if isinstance(supabase_result, dict) else supabase_result is not None
            }
            
            # Include Supabase error details if save failed
            if isinstance(supabase_result, dict) and not supabase_result.get("success"):
                response_data["supabase_error"] = supabase_result.get("error", "Unknown error")
            
            return response_data
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
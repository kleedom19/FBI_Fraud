from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from PIL import Image 
import os
from pathlib import Path
import tempfile

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
                    output_path = os.path.join(tmpdir, f"page_{i}_output")

                    # Run OCR inference
                    model.infer(
                        tokenizer,
                        prompt=prompt,
                        image_file=image_path,
                        output_path=output_path,
                        base_size=1024,
                        image_size=640,
                        crop_mode=True,
                        save_results=True,
                        test_compress=True
                    )

                    # Read results
                    output_file = Path(output_path)
                    if output_file.exists():
                        with open(output_file, "r", encoding="utf-8") as f:
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
                            "error": "OCR output file not found"
                        })
                        
                except Exception as e:
                    results.append({
                        "page": i,
                        "text": "",
                        "status": "error",
                        "error": str(e)
                    })

            return {
                "filename": file.filename,
                "total_pages": len(images),
                "results": results
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

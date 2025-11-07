from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from PIL import Image 
import os
import shutil 
from deepseekOcr import model, tokenizer
from pathlib import Path
import tempfile

TOKEN_ID = os.getenv("TOKEN_ID")
TOKEN_SECRET = os.getenv("TOKEN_SECRET")

app = FastAPI(title="Deepseek OCR Modal Endpoint")

@app.post("/ocr/pdf")
async def ocr_pdf(file: UploadFile = File(...)):

    if not file.filename.endswith(".pdf"):
        return JSONResponse({"error": "File must be a PDF."}, status_code=400)

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)

        results = []
        for i, img in enumerate(images):
            image_path = os.path.join(tmpdir, f"page_{i+1}.png")
            img.save(image_path, "PNG")

            prompt = "<image>\n<|grounding|>Convert the document to markdown. "
            output_path = os.path.join(tmpdir, f"page_{i+1}_output.md")

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

            if Path(output_path).exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    results.append(f.read())
            else:
                results.append("Error: OCR failed for this page.")

    return {"filename": file.filename, "ocr_results": results}

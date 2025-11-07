import modal
from pathlib import Path
import os
import uvicorn


# Modal App Definition
app = modal.App("deepseek-ocr")

# Paths
ocr_script_local_path = Path(__file__).parent / "ocr_endpoint.py"
ocr_script_remote_path = "/root/ocr_endpoint.py"
deepseek_local_path = Path(__file__).parent / "deepseekOcr.py"
deepseek_path_remote = "/root/deepseekOcr.py"

# Sanity checks
if not ocr_script_local_path.exists():
    raise RuntimeError("Missing ocr_endpoint.py — check your file path.")
if not deepseek_local_path.exists():
    raise RuntimeError("Missing deepseekOcr.py — check your file path.")

# Build Modal Image
image = (
    modal.Image.debian_slim(python_version="3.10")  
    .apt_install("poppler-utils")  
    .pip_install(
        "fastapi",
        "uvicorn",
        "pdf2image",
        "pillow",
        "transformers>=4.44.2,<4.46",
        "torch>=2.3",
        "safetensors>=0.4",
        "accelerate",
        "python-multipart",  
    )
    .add_local_file(ocr_script_local_path, ocr_script_remote_path)
    .add_local_file(deepseek_local_path, deepseek_path_remote)
)

# Optional Secret Test Function
@app.function(secrets=[modal.Secret.from_name("deepseek-secrets")])
def check_secrets():
    token_id = os.getenv("TOKEN_ID")
    token_secret = os.getenv("TOKEN_SECRET")
    if not token_id or not token_secret:
        raise RuntimeError("Missing TOKEN_ID or TOKEN_SECRET in secrets.")
    print(f"TOKEN_ID starts with: {token_id[:4]}****")
    print(f"TOKEN_SECRET starts with: {token_secret[:4]}****")
    return {"ok": True}

# FastAPI OCR Server
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("deepseek-secrets")],
    gpu="A10G",                
    min_containers=1,           
    max_containers=2,           
    timeout=600,                
)
@modal.fastapi_endpoint()       
def serve():
    """Runs the DeepSeek-OCR FastAPI server on Modal."""
    token_id = os.getenv("TOKEN_ID")
    token_secret = os.getenv("TOKEN_SECRET")

    print("Starting DeepSeek OCR endpoint...")
    print(f"Using token: {token_id[:4]}****")

    # Run FastAPI with Uvicorn
    uvicorn.run(
        "ocr_endpoint:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

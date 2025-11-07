import modal
from pathlib import Path
import os


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
    .uv_pip_install(
        "fastapi",
        "uvicorn",
        "pdf2image",
        "pillow",
        "transformers>=4.44.2,<4.46",
        "torch>=2.3",
        "torchvision>=0.18.0",
        "safetensors>=0.4",
        "accelerate",
        "python-multipart",
        "addict>=2.4.0",
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
    container_idle_timeout=300,  # Keep container warm for 5 minutes
    timeout=600,                
)
@modal.asgi_app()
def serve():
    """Returns the DeepSeek-OCR FastAPI app for Modal to serve."""
    import sys
    sys.path.insert(0, "/root")
    
    from ocr_endpoint import app as fastapi_app
    
    print("DeepSeek OCR endpoint initialized successfully!")
    
    return fastapi_app

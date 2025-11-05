import modal
from pathlib import Path
import os
import uvicorn

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
    raise RuntimeError("Missing local deepseekOcr file — check your file path.")

# Build Modal image
image = (
    modal.Image.debian_slim(python_version="3.9")
    .pip_install(
        "fastapi",
        "uvicorn",
        "pdf2image",
        "pillow",
        "transformers>=4.44.2,<4.46",
        "torch>=2.3",
        "safetensors>=0.4",
        "accelerate",
    )
    .add_local_file(ocr_script_local_path, ocr_script_remote_path)
    .add_local_file(deepseek_local_path, deepseek_path_remote)  # <-- corrected line
)

# Optional helper function to check secrets
@app.function(secrets=[modal.Secret.from_name("deepseek-secrets")])
def some_function():
    token_id = os.getenv("TOKEN_ID")
    token_secret = os.getenv("TOKEN_SECRET")
    print("TOKEN_ID (masked):", token_id[:4] + "****")
    print("TOKEN_SECRET (masked):", token_secret[:4] + "****")
    return {"token_id": token_id, "token_secret": token_secret}

# Main OCR FastAPI server
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("deepseek-secrets")],
    concurrency_limit=50,  # max concurrent requests
)
@modal.concurrent(max_inputs=50)
@modal.web_server(8000)
def run():
    """Start the OCR FastAPI app on port 8000"""
    token_id = os.getenv("TOKEN_ID")
    token_secret = os.getenv("TOKEN_SECRET")
    
    print("Loaded tokens:", token_id[:4] + "****")  # sanity check

    # Run uvicorn directly instead of subprocess
    uvicorn.run("ocr_endpoint:app", host="0.0.0.0", port=8000)

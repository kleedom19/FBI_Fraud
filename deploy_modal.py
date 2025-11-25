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

cuda_version = "11.8"  # should be no greater than host CUDA version
flavor = "devel"  # includes full CUDA toolkit
operating_sys = "ubuntu24.04"
tag = f"{cuda_version}-{flavor}-{operating_sys}"
HF_CACHE_PATH = "/cache"

# Build Modal Image
image = (
    modal.Image.from_registry("nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04", add_python="3.12") 
    .apt_install("poppler-utils","git","build-essential")  
    .uv_pip_install(
        # FastAPI web framework
        "fastapi",
        "uvicorn",
        "python-multipart",
        # PDF and image processing
        "pdf2image",
        "pillow",
        # PyTorch and vision
        "torch==2.6.0",
        "torchvision>=0.18.0",
        # Transformers and tokenizers
        "transformers==4.46.3",
        "tokenizers==0.20.3",
        # Model dependencies
        "safetensors>=0.4",
        "accelerate",
        "einops",
        # Config helpers
        "addict>=2.4.0",
        "easydict",
        "wheel",
        "setuptools",
        "hf_transfer",
        # Gemini API
        "google-generativeai",
        # Supabase
        "supabase",
        "python-dotenv",
        # Data processing
        "pandas",
    )
    .run_commands(
        "pip install flash-attn==2.7.3 --no-build-isolation"
    )
    .env({"HF_HUB_CACHE": HF_CACHE_PATH, "HF_HUB_ENABLE_HF_TRANSFER": "1", "PMIX_MCA_gds": "hash"})
    .add_local_file(ocr_script_local_path, ocr_script_remote_path)
    .add_local_file(deepseek_local_path, deepseek_path_remote)
)

# Optional Secret Test Function
@app.function(secrets=[modal.Secret.from_name("deepseek-secrets")])
def check_secrets():
    token_id = os.getenv("TOKEN_ID")
    token_secret = os.getenv("TOKEN_SECRET")
    gemini_key = os.getenv("GEMINI_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not token_id or not token_secret:
        raise RuntimeError("Missing TOKEN_ID or TOKEN_SECRET in secrets.")
    if not gemini_key:
        raise RuntimeError("Missing GEMINI_API_KEY in secrets.")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY/SUPABASE_SERVICE_KEY in secrets.")
    
    print(f"TOKEN_ID starts with: {token_id[:4]}****")
    print(f"TOKEN_SECRET starts with: {token_secret[:4]}****")
    print(f"GEMINI_API_KEY starts with: {gemini_key[:4]}****")
    print(f"SUPABASE_URL: {supabase_url[:20]}****")
    return {"ok": True}

# FastAPI OCR Server
@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("deepseek-secrets"),
        modal.Secret.from_name("gemini-supabase-secrets")
    ],
    gpu="A10G",                
    scaledown_window=300,  # Keep container warm for 5 minutes
    timeout=600,                
)
@modal.asgi_app()
def serve():
    """Returns the DeepSeek-OCR FastAPI app for Modal to serve."""
    import sys
    sys.path.insert(0, "/root")
    
    from ocr_endpoint import app as fastapi_app
    
    print("DeepSeek OCR endpoint initialized successfully!")
    print("Gemini and Supabase integration ready!")
    
    return fastapi_app

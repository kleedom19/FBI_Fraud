import modal
from ocr_endpoint import app as fastapi_app

modal_app = modal.App("deepseek-ocr")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi",
        "uvicorn",
        "pdf2image",
        "pillow",
        "transformers>=4.44.2,<4.46",
        "torch>=2.3",
        "safetensors>=0.4",
        "accelerate"
    )
    .apt_install("poppler-utils")
)

@modal_app.function(image=image, gpu="A10G", min_containers=1)
@modal.asgi_app()
def serve():
    import os
    os.environ["MODAL_ENV"] = "1"  # enable GPU batching in deepseekOcr.py
    return fastapi_app

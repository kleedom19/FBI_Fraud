from transformers import AutoTokenizer, AutoModel
import torch
from PIL import Image

print("🔹 Loading DeepSeek-OCR model...")

device = "cpu"  # always CPU locally, Modal GPU will override

tokenizer = AutoTokenizer.from_pretrained(
    "deepseek-ai/DeepSeek-OCR",
    trust_remote_code=True
)

model = AutoModel.from_pretrained(
    "deepseek-ai/DeepSeek-OCR",
    trust_remote_code=True,
    torch_dtype=torch.float32,
    low_cpu_mem_usage=True
).to(device).eval()

print(f"Model loaded on {device.upper()}")

# Batching
def infer_batch(images, prompt="<image>\n<|grounding|>Convert the document to markdown. "):
    """
    images: list of PIL.Image objects
    Returns list of OCR text outputs.
    """
    results = []

    for img in images:
        # Each image is processed individually
        output_path = None  
        text = model.infer(
            tokenizer,
            prompt=prompt,
            image_file=img,   
            output_path=output_path,
            base_size=1024,
            image_size=640,
            crop_mode=True,
            save_results=False,
            test_compress=False
        )
        results.append(text)

    return results

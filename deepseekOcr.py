"""
DeepSeek-OCR Model Module
Loads the model once and exports it for use by the API endpoint.
"""
from transformers import AutoModel, AutoTokenizer
import torch

print("Loading DeepSeek-OCR model... This may take a few minutes on first run.")

MODEL_NAME = 'deepseek-ai/DeepSeek-OCR'

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME, 
    trust_remote_code=True
)

# Load model
model = AutoModel.from_pretrained(
    MODEL_NAME,
    _attn_implementation='flash_attention_2',
    trust_remote_code=True,
    use_safetensors=True
)

# Move to GPU and set to eval mode
model = model.eval().cuda().to(torch.bfloat16)

print("DeepSeek-OCR model loaded successfully!")


"""Checks which Hugging Face models answer with YOUR token. Run: python test_hf.py"""
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
 
load_dotenv()
token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
print("Token found:", bool(token))
 
CANDIDATES = [
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "mistralai/Mistral-Nemo-Instruct-2407",
]
 
for model in CANDIDATES:
    try:
        client = InferenceClient(model=model, token=token)
        r = client.chat_completion(
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            max_tokens=10,
        )
        print(f"WORKS  {model} -> {r.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"FAILS  {model} -> {str(e).splitlines()[-1][:120]}")
 
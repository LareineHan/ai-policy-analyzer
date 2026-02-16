# check_models.py

import google.genai as genai
from google.genai import types
import os

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
    http_options=types.HttpOptions(api_version='v1alpha')
)

print("Available models:")
for model in client.models.list():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  ✓ {model.name}")
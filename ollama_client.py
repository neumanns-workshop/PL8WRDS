"""
Ollama client for PL8WRDS ranking generation.
Based on general_solutions template patterns.
"""

import subprocess
import httpx
from openai import OpenAI
from typing import Any
from pydantic import BaseModel

class OllamaClient:
    """Client for interacting with local Ollama instance."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = OpenAI(
            base_url=f"{base_url}/v1",
            api_key="ollama"  # Required but unused for local
        )
    
    def generate_response(self, model: str, prompt: str, response_model: BaseModel, **kwargs) -> Any:
        """Generate structured response using Pydantic model."""
        # Set temperature to 0.01 (closest to 0 as most models allow) for deterministic scoring
        if 'temperature' not in kwargs:
            kwargs['temperature'] = 0.01
        
        parsed_response = self.client.beta.chat.completions.parse(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_model,
            **kwargs
        )
        return parsed_response.choices[0].message.parsed

def check_ollama_health(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama server is running."""
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        response.raise_for_status()
        return True
    except (httpx.RequestError, httpx.HTTPStatusError):
        return False

def check_model_available(model: str, base_url: str = "http://localhost:11434") -> bool:
    """Check if model is available locally."""
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        response.raise_for_status()
        models = response.json().get("models", [])
        return any(model in m["name"] for m in models)
    except (httpx.RequestError, httpx.HTTPStatusError):
        return False

def auto_setup_model(model: str) -> bool:
    """Check and download model if needed."""
    if not check_ollama_health():
        print("❌ Ollama not running. Start with: ollama serve")
        return False
    
    if check_model_available(model):
        print(f"✅ Model '{model}' available")
        return True
    
    print(f"📥 Downloading '{model}'...")
    try:
        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            check=True,
            timeout=600
        )
        print(f"✅ Model '{model}' downloaded")
        return True
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        return False

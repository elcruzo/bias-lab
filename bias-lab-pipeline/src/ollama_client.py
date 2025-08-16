"""
Ollama client for local LLM inference.
"""

import json
import requests
from typing import Dict, Optional


class OllamaClient:
    """Client for Ollama local LLM."""
    
    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def check_health(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def complete(self, prompt: str, temperature: float = 0.2, max_tokens: int = 500) -> str:
        """Generate completion using Ollama."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            }
            
            response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                raise Exception(f"Ollama error: {response.status_code}")
                
        except Exception as e:
            print(f"Ollama request failed: {e}")
            raise
    
    def complete_json(self, prompt: str, temperature: float = 0.2) -> Dict:
        """Generate JSON completion using Ollama."""
        # Add JSON instruction to prompt
        json_prompt = prompt + "\n\nRespond ONLY with valid JSON, no other text."
        
        response = self.complete(json_prompt, temperature)
        
        # Try to extract JSON from response
        try:
            # Find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback if no JSON found
                return {"error": "No JSON in response", "raw": response}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": response}


def test_ollama():
    """Test if Ollama is working."""
    client = OllamaClient()
    
    print("🦙 Testing Ollama...")
    
    if not client.check_health():
        print("❌ Ollama is not running!")
        print("   Install: curl -fsSL https://ollama.ai/install.sh | sh")
        print("   Then run: ollama pull mistral")
        print("   Start server: ollama serve")
        return False
    
    print("✅ Ollama is running")
    
    # Test completion
    try:
        response = client.complete("What is 2+2? Answer in one word.")
        print(f"✅ Test completion: {response[:50]}")
        
        # Test JSON
        json_response = client.complete_json('{"question": "What is 2+2?", "answer":')
        print(f"✅ JSON response: {json_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False


if __name__ == "__main__":
    test_ollama()

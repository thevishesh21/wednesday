"""
WEDNESDAY AI OS — Vision Model
Interface for LLaVA (Ollama) or GPT-4o Vision.
"""
import base64
import requests
import os
from core.logger import get_logger
from core.config_loader import cfg

log = get_logger("vision.model")

class VisionModel:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llava"

    def describe_image(self, image_path: str, prompt: str = "What is in this image?") -> str:
        """Analyze an image using a vision model."""
        if not os.path.exists(image_path):
            return "Error: Image file not found."

        try:
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')

            # Try Ollama (LLaVA)
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "images": [img_data]
            }
            
            log.info(f"Analyzing image {image_path} with {self.model}...")
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json().get("response", "No description generated.")
            else:
                return f"Vision Error: Ollama returned {response.status_code}"

        except Exception as e:
            log.error(f"Vision analysis failed: {e}")
            return f"Error during vision analysis: {str(e)}"

vision_model = VisionModel()

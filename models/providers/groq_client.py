import requests
from models.base_client import BaseLLMClient

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient(BaseLLMClient):
    """
    LLM client for Groq's ultra-fast inference API.
    Uses raw HTTP requests to avoid dependency conflicts with openai==0.28.
    """
    def __init__(self, api_key: str, model_name: str = 'llama-3.3-70b-versatile'):
        self.api_key = api_key
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def generate_action(self, prompt: str, image_path: str) -> str:
        import base64
        with open(image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 300,
        }

        resp = requests.post(GROQ_API_URL, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def generate_text(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }

        resp = requests.post(GROQ_API_URL, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

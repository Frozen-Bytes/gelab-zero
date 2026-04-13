import google.generativeai as genai
from models.base_client import BaseLLMClient

class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model_name='gemini-1.5-flash'):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_action(self, prompt: str, image_path: str) -> str:
        from PIL import Image
        img = Image.open(image_path)
        response = self.model.generate_content([prompt, img])
        return response.text if response else ''
    
    def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text if response else ''

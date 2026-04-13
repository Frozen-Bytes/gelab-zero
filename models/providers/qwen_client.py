# models/providers/qwen_client.py
import os
from openai import OpenAI  # Uses OpenAI-compatible endpoint
from models.base_client import BaseLLMClient

class QwenClient(BaseLLMClient):
    def __init__(
        self, 
        api_key: str, 
        model_name: str = 'qwen-plus',
        region: str = 'singapore'  # Options: 'singapore', 'us', 'beijing', 'hongkong'
    ):
        """
        Initialize Qwen client via DashScope OpenAI-compatible API.
        
        Args:
            api_key: Your DashScope API key (sk-xxx)
            model_name: Model identifier (e.g., 'qwen-plus', 'qwen-turbo', 'qwen3-vl-plus')
            region: Deployment region for lower latency
        """
        # Region-specific base URLs [[45]]
        base_urls = {
            'singapore': 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1',
            'us': 'https://dashscope-us.aliyuncs.com/compatible-mode/v1',
            'beijing': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'hongkong': 'https://cn-hongkong.dashscope.aliyuncs.com/compatible-mode/v1'
        }
        
        self.base_url = base_urls.get(region.lower(), base_urls['singapore'])
        self.model_name = model_name
        
        # Initialize OpenAI client with DashScope endpoint
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )

    def generate_action(self, prompt: str, image_path: str) -> str:
        """
        Takes a text prompt and an image path, returns response from Qwen-VL model.
        Requires a multimodal model like 'qwen3-vl-plus'.
        """
        import base64
        
        # Encode image to base64 for API [[59]]
        with open(image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Use multimodal endpoint with image_url format
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{base64_image}'
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )
        
        return response.choices[0].message.content or ''
    
    def generate_text(self, prompt: str) -> str:
        """For text-only generation scenarios."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.0,
            max_tokens=500,
        )
        return response.choices[0].message.content or ''
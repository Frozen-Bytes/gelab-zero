from openai import OpenAI
from models.base_client import BaseLLMClient


class OpenRouterClient(BaseLLMClient):
    """
    LLM client for OpenRouter (OpenAI-compatible API).
    Supports any model available on OpenRouter (Claude, Llama, Gemini, etc.)
    """
    def __init__(self, api_key: str, model_name: str = 'anthropic/claude-sonnet-4'):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model_name = model_name

    def generate_action(self, prompt: str, image_path: str) -> str:
        import base64
        with open(image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

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
                                'url': f'data:image/png;base64,{base64_image}'
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        return response.choices[0].message.content

    def generate_text(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content

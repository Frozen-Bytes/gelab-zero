import os
from models.providers.gemini_client import GeminiClient
from models.providers.openai_client import OpenAIClient
from models.providers.qwen_client import QwenClient

from dotenv import load_dotenv

load_dotenv()

def get_llm_client(llm_config: dict):
    '''
    Returns the instantiated client based on the YAML config.
    '''
    provider = llm_config.get('provider').lower()
    model_name = llm_config.get('model_name')

    if provider == 'gemini':
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError('GEMINI_API_KEY not found in .env')
        
        return GeminiClient(api_key=api_key, model_name=model_name)
    
    elif provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY not found in .env')
        
        return OpenAIClient(api_key=api_key, model_name=model_name)
           
    else:
        raise ValueError(f'Unsupported LLM provider: {provider}')

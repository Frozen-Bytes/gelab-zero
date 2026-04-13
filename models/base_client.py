from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    '''
    Abstract base class for all LLM providers.
    '''
    @abstractmethod
    def generate_action(self, prompt: str, image_path: str) -> str:
        '''
        Takes a text prompt and an image path, and returns the raw string response from the LLM.
        '''
        pass

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        '''For Scenario Generation (Text Only)'''
        pass

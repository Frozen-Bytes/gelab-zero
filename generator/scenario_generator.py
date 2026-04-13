from utils.logger import setup_logger
from .prompts import build_goal_prompt

logger = setup_logger("scenario_generator")

class ScenarioGenerator:
    def __init__(self, llm_client):
        """Inject any generic LLM client here."""
        self.llm_client = llm_client

    def generate_scenarios(self, app_summary: str) -> list[str]:
        logger.info("Generating scenarios using the generic LLM client...")
        prompt = build_goal_prompt(app_summary)
        
        try:
            # We use the text-only method
            raw_text = self.llm_client.generate_text(prompt)
            
            # Clean up the response into a list
            goals = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]
            return goals
        except Exception as e:
            logger.error(f"Scenario Generation Error: {e}")
            return []
"""
GENERATOR/PROMPTS.PY
This module handles the 'Prompt Engineering' for the testing phase.
It defines the persona, rules, and formatting that Qwen must follow.
"""

SYSTEM_PROMPT = """You are a mobile app testing planner.
Your job is to read a description of an Android app and generate a list of realistic user goals to simulate.

Rules:
- Each goal must be a single actionable sentence starting with a verb (e.g. "Open", "Search", "Send", "Enable", "View")
- Goals should reflect what a real user would actually want to do in this app
- Goals should be diverse - cover different features of the app
- Do NOT repeat similar goals
- Do NOT include specific private data (e.g. "login with password abc123")
- Output ONLY a numbered list, nothing else. No explanation, no preamble.

Example output format:
1. Open the list view and scroll through all available items 
2. Open the settings and toggle Dark Mode on
3. Search for 'Privacy' in the search bar
4. View the current version number in the About section"""


def build_goal_prompt(app_summary: str, num_goals: int = 3) -> str:
    """
    Constructs the final prompt string sent to the LLM (Qwen).
    
    Args:
        app_summary (str): The condensed text containing features/permissions 
                           extracted from the APK/Manifest.
        num_goals (int): Number of independent goals to generate (clamped to 2-10).
    
    Returns:
        str: A fully formatted instruction block ready for Qwen API.
    """
    # Clamp input to reasonable bounds to save tokens and ensure quality
    safe_num_goals = max(2, min(10, num_goals))
    
    return f"""{SYSTEM_PROMPT}

### APP CONTEXT (Extracted Metadata):
{app_summary}

### INSTRUCTION:
Generate exactly {safe_num_goals} independent user navigation goals based on the context above.

Goals:"""
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
- Each `task_description` must be a **multi-step user journey** (2–4 actions), not a single tap
- Chain actions using ", then" to show sequence: "Open X, then tap Y, then verify Z"
- Do NOT include specific private data (e.g. "login with password abc123")
- task_name must be CamelCase, concise, and suitable for use as a test file name (e.g. "RecordAudioClip", "ToggleDarkMode")
- Output ONLY a valid JSON array, nothing else. No explanation, no preamble, no markdown backticks.

Output format:
[
  {
    "task_name": "ShortCamelCaseName",
    "task_description": "Actionable goal sentence starting with a verb."
  }
]

Example output:
[
  {
    "task_name": "ScrollItemListView",
    "task_description": "Open the list view and scroll through all available items."
  },
  {
    "task_name": "ToggleDarkMode",
    "task_description": "Open the settings and toggle Dark Mode on."
  },
  {
    "task_name": "SearchPrivacySettings",
    "task_description": "Search for 'Privacy' in the search bar."
  },
  {
    "task_name": "ViewAppVersion",
    "task_description": "View the current version number in the About section."
  }
]"""


def build_goal_prompt(app_summary: str, num_goals: int = 3) -> str:
    """
    Constructs the final prompt string sent to the LLM.
    
    Args:
        app_summary (str): The condensed text containing features/permissions 
                           extracted from the APK/Manifest.
        num_goals (int): Number of independent goals to generate (clamped to 2-10).
    
    Returns:
        str: A fully formatted instruction block ready for Qwen API.
    """
    # Clamp input to reasonable bounds to save tokens and ensure quality
    safe_num_goals = num_goals
    
    return f"""{SYSTEM_PROMPT}

### APP CONTEXT (Extracted Metadata):
{app_summary}

### INSTRUCTION:
Generate exactly {safe_num_goals} independent user navigation goals based on the context above.

Goals:"""
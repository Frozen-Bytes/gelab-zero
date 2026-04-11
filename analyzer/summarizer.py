"""
CORE/ANALYZER/SUMMARIZER.PY
This module converts technical APK features into a human-readable summary.
The output of this file serves as the primary context for Gemini when it 
needs to decide what testing goals to create.
"""

from utils.logger import setup_logger

logger = setup_logger("summarizer")

def summarize_features(features: dict) -> str:
    """
    Transforms a complex dictionary of APK features into a formatted string.
    
    Why we do this: 
    Raw dictionaries often contain too much 'noise' or 'tokens' for an LLM. 
    By picking the most important parts and joining them with labels, we 
    make the AI much more accurate.

    Args:
        features (dict): The master dictionary produced by the Extractor.
        
    Returns:
        str: A clean, multi-line string briefing for the AI.
    """

    logger.info("Generating natural language summary for AI context")
    lines = []

    if features.get("package"):
        lines.append(f"Package: {features['package']}")

    if features.get("activities"):
        lines.append(f"Activities: {', '.join(features['activities'][:20])}")

    if features.get("permissions"):
        lines.append(f"Permissions: {', '.join(features['permissions'][:15])}")

    if features.get("intent_actions"):
        lines.append(f"Intent actions: {', '.join(features['intent_actions'][:10])}")

    if features.get("ui_strings"):
        lines.append(f"UI labels: {', '.join(features['ui_strings'][:30])}")

    if features.get("classes"):
        lines.append(f"Key classes: {', '.join(features['classes'][:20])}")

    if features.get("methods"):
        lines.append(f"Key methods: {', '.join(features['methods'][:20])}")

    summary = "\n".join(lines)
    logger.debug("Summary generated successfully.")
    return summary
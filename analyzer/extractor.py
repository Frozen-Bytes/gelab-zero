"""
CORE/ANALYZER/EXTRACTOR.PY
This module is the high-level coordinator for the analysis phase.
It calls all specialized parsing functions and bundles their results into 
a structured "Feature Map" of the Android application.
"""

from utils.logger import setup_logger
from .parser import parse_manifest, parse_strings, parse_smali

logger = setup_logger("extractor")

def extract_apk_features(apk_dir: str) -> dict:
    """
    Executes a full scan of a decompiled APK directory.
    
    Args:
        apk_dir (str): The path to the folder containing the decompiled APK files.
        
    Returns:
        dict: A comprehensive dictionary containing:
              - package: The unique app identifier.
              - activities: Screen names found in the code.
              - permissions: Security rights requested by the app.
              - intent_actions: External communication hooks.
              - ui_strings: Human-readable text found in the UI.
              - classes/methods: Logical building blocks from the code.
    """

    logger.info(f"--- Starting Feature Extraction: {apk_dir} ---")
    
    manifest = parse_manifest(apk_dir)
    strings = parse_strings(apk_dir)
    
    # Pass app package to smali parser so it doesn't accidentally skip app code
    app_package = manifest.get("package", "")
    smali = parse_smali(apk_dir, app_package=app_package)

    features = {
        "package": app_package,
        "activities": manifest.get("activities", []),
        "permissions": manifest.get("permissions", []),
        "intent_actions": manifest.get("intent_actions", []),
        "ui_strings": strings,
        "classes": smali.get("classes", []),
        "methods": smali.get("methods", []),
        "navigation_routes": smali.get("navigation_routes", []),
        "content_descriptions": smali.get("content_descriptions", []),
    }
    
    # Log specific findings so you see them in the console
    logger.info(f"Extraction complete for: {features['package']}")
    logger.info(f"Activities found: {len(features['activities'])} {features['activities']}")
    logger.info(f"UI Labels found: {len(features['ui_strings'])}")
    logger.info(f"Classes found: {len(features['classes'])}")
    logger.info(f"Methods found: {len(features['methods'])}")
    if features['navigation_routes']:
        logger.info(f"Navigation routes found: {len(features['navigation_routes'])} {features['navigation_routes']}")
    if features['content_descriptions']:
        logger.info(f"Content descriptions found: {len(features['content_descriptions'])}")
    
    return features
"""
CORE/ANALYZER/TEST_ANALYZER.PY
This is the main entry point for testing feature extraction and parsing in the system.
"""

import os
from utils.apk_utils import decode_apk
from core.analyzer.extractor import extract_apk_features
from core.analyzer.summarizer import summarize_features
from utils.logger import setup_logger

logger = setup_logger("test_suite")

def run_real_test():
    apk_folder = os.path.join("data", "apks")
    
    # Find the first available .apk file
    apk_files = [f for f in os.listdir(apk_folder) if f.endswith(".apk")]
    
    if not apk_files:
        logger.error(f"No .apk files found in {apk_folder}. Please drop an APK there!")
        return

    target_apk = os.path.join(apk_folder, apk_files[0])
    apk_name = os.path.splitext(apk_files[0])[0]
    decoded_output = os.path.join(apk_folder, f"decoded_{apk_name}")

    logger.info(f"--- Starting Real Application Test: {apk_files[0]} ---")

    try:
        # 1. Decode
        decode_apk(target_apk, decoded_output)

        # 2. Extract (using the code we fixed earlier)
        features = extract_apk_features(decoded_output)

        # 3. Summarize
        summary = summarize_features(features)

        print("\n" + "="*50)
        print("REAL APPLICATION SUMMARY")
        print("="*50)
        print(summary)
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    run_real_test()
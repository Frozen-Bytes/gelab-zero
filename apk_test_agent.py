"""
APK_TEST_AGENT.PY
Entry point for APK analysis.
Validates an APK, decodes it with apktool, extracts app features, and summarizes the result.
"""

import argparse
import os
import sys

from analyzer.extractor import extract_apk_features
from analyzer.summarizer import summarize_features
from utils.apk_utils import decode_apk, prepare_output_dir, validate_apk_path
from utils.logger import setup_logger

logger = setup_logger("apk_test_agent")


def main() -> int:
    parser = argparse.ArgumentParser(description="APK Analysis: validate, decode, extract, summarize")
    parser.add_argument("apk_path", help="Path to the APK file")
    parser.add_argument("--output_dir", default=None, help="Output directory for decoded APK")

    args = parser.parse_args()

    try:
        validate_apk_path(args.apk_path)
    except Exception as exc:
        logger.error(exc)
        print(f"Error: {exc}")
        return 1

    output_dir = prepare_output_dir(args.output_dir)
    logger.info(f"Using decode output folder: {output_dir}")

    try:
        decoded_dir = decode_apk(args.apk_path, output_dir)
        logger.info(f"APK decoded to: {decoded_dir}")
    except Exception as exc:
        logger.error(f"APK decode failed: {exc}")
        print(f"Error decoding APK: {exc}")
        return 1

    try:
        features = extract_apk_features(decoded_dir)
        logger.info("Feature extraction completed.")
    except Exception as exc:
        logger.error(f"Feature extraction failed: {exc}")
        print(f"Error extracting APK features: {exc}")
        return 1

    try:
        summary = summarize_features(features)
        logger.info("Feature summarization completed.")
    except Exception as exc:
        logger.error(f"Feature summarization failed: {exc}")
        print(f"Error summarizing APK features: {exc}")
        return 1

    print("\n=== APK Analysis Summary ===")
    print(summary)
    print(f"\nDecoded directory: {decoded_dir}")
    print("==============================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

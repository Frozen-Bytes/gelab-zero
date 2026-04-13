"""
APK_TEST_AGENT.PY
Entry point for APK analysis.
Validates an APK, decodes it with apktool, extracts app features, summarizes the result,
and generates test scenarios using an LLM.
"""

import argparse
import os
import sys
import yaml

from analyzer.extractor import extract_apk_features
from analyzer.summarizer import summarize_features
from generator.scenario_generator import ScenarioGenerator
from models.factory import get_llm_client
from utils.apk_utils import decode_apk, prepare_output_dir, validate_apk_path
from utils.logger import setup_logger

logger = setup_logger("apk_test_agent")


def load_settings():
    """Load configuration from settings.yaml"""
    try:
        with open("configs/settings.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load settings.yaml: {e}")
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="APK Analysis: validate, decode, extract, summarize, and generate scenarios")
    parser.add_argument("apk_path", help="Path to the APK file")
    parser.add_argument("--output_dir", default=None, help="Output directory for decoded APK")
    parser.add_argument("--skip_execution", action="store_true", help="Skip scenario execution on device")
    parser.add_argument("--num_goals", type=int, default=3, help="Number of test scenarios to generate (default: 3)")

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

    # Generate scenarios
    try:
        config = load_settings()
        gen_config = config.get("scenario_gen", {})
        
        if gen_config:
            logger.info("Initializing scenario generator...")
            client = get_llm_client(gen_config)
            generator = ScenarioGenerator(llm_client=client)
            
            logger.info("Generating test scenarios...")
            scenarios = generator.generate_scenarios(summary, num_goals=args.num_goals)
            
            print("\n=== Generated Test Scenarios ===")
            if scenarios:
                for i, scenario in enumerate(scenarios, 1):
                    print(f"{i}. [{scenario['task_name']}] {scenario['task_description']}")
            else:
                print("No scenarios generated.")
            print("================================\n")
        else:
            logger.warning("Scenario generation config not found in settings.yaml")
    except Exception as exc:
        logger.warning(f"Scenario generation failed: {exc}")
        print(f"Warning: Could not generate scenarios: {exc}\n")
        return 0  # Continue even if generation fails

    # Execute scenarios if not skipped
    if not args.skip_execution and scenarios:
        try:
            from copilot_agent_client.pu_client import evaluate_task_on_device
            from copilot_front_end.mobile_action_helper import list_devices, get_device_wm_size
            from copilot_agent_server.local_server import LocalServer
            from utils.apk_utils import ensure_device_connected, install_apk_on_device

            tmp_server_config = {
                "log_dir": "running_log/server_log/os-copilot-local-eval-logs/traces",
                "image_dir": "running_log/server_log/os-copilot-local-eval-logs/images",
                "debug": False
            }

            local_model_config = {
                "task_type": "parser_0922_summary",
                "model_config": {
                    "model_name": "gelab-zero-4b-preview",
                    "model_provider": "local",
                    "args": {
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "frequency_penalty": 0.0,
                        "max_tokens": 4096,
                    },
                },
                "max_steps": 400,
                "delay_after_capture": 2,
                "debug": False
            }

            device_id = list_devices()[0]
            device_wm_size = get_device_wm_size(device_id)
            device_info = {
                "device_id": device_id,
                "device_wm_size": device_wm_size
            }

            # Ensure device is connected
            ensure_device_connected(device_id)

            # Install APK on device
            print(f"Installing APK on device: {device_id}")
            install_apk_on_device(device_id, args.apk_path)

            l2_server = LocalServer(tmp_server_config)
            tmp_rollout_config = local_model_config

            # Prepend package name to scenarios
            package_name = features.get("package", "")

            print(f"Executing {len(scenarios)} scenarios on device: {device_id}")
            for i, scenario in enumerate(scenarios, 1):
                # Add package name at the start of every scenario
                task_name = scenario['task_name']
                task_description = scenario['task_description']
                task_with_package = f"{package_name}: {task_description}"
                print(f"\n{'='*50}")
                print(f"Executing Scenario {i}/{len(scenarios)}: {task_with_package}")
                print(f"{'='*50}")

                try:
                    evaluate_task_on_device(l2_server, device_info, task_with_package, tmp_rollout_config, extra_info={"file_name":task_name} ,reflush_app=True)
                    print(f"Scenario {i} completed successfully.")
                except Exception as e:
                    print(f"Error executing scenario {i} '{task_with_package}': {e}")
                    # Continue to next scenario

            print("\nAll scenarios executed.")
        except Exception as exc:
            logger.error(f"Execution setup failed: {exc}")
            print(f"Error setting up execution: {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

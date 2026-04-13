import os
import yaml
from analyzer.extractor import extract_apk_features
from analyzer.summarizer import summarize_features
from models.factory import get_llm_client
from generator.scenario_generator import ScenarioGenerator
from utils.logger import setup_logger

logger = setup_logger("test_generator")

def load_settings():
    with open("configs/settings.yaml", "r") as f:
        return yaml.safe_load(f)

def run_end_to_end_test():
    # 1. Setup Data
    apk_folder = os.path.join("data", "apks")
    decoded_folders = [f for f in os.listdir(apk_folder) if f.startswith("decoded_")]
    if not decoded_folders: return

    target_path = os.path.join(apk_folder, decoded_folders[0])
    
    # 2. Extract and Summarize
    features = extract_apk_features(target_path)
    summary = summarize_features(features)


    config = load_settings()
    # Pull the config for 'scenario_gen' specifically
    gen_config = config.get("scenario_gen", {}) 
    
    try:
        client = get_llm_client(gen_config)
        
        # Inject it
        generator = ScenarioGenerator(llm_client=client)
        goals = generator.generate_scenarios(summary)

        print("\n" + "="*50)
        print(f"GENERATED SCENARIOS (via {gen_config['provider']})")
        print("="*50)
        for goal in goals:
            print(f" -> {goal}")
        print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"Generator test failed: {e}")

if __name__ == "__main__":
    run_end_to_end_test()
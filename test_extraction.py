"""Quick test of the fixed extractor against the decoded NIA APK."""
import os
from analyzer.extractor import extract_apk_features

decoded_dir = r"C:\Users\Kareem Essam\AppData\Local\Temp\apk_decode_rgpua830"

if not os.path.exists(decoded_dir):
    print(f"Decoded dir not found: {decoded_dir}")
    exit(1)

features = extract_apk_features(decoded_dir)

print("\n=== CLASSES (first 30) ===")
for c in features["classes"][:30]:
    print(f"  {c}")
print(f"Total classes: {len(features['classes'])}")

print("\n=== METHODS (first 30) ===")
for m in features["methods"][:30]:
    print(f"  {m}")
print(f"Total methods: {len(features['methods'])}")

print("\n=== NAVIGATION ROUTES ===")
for r in features.get("navigation_routes", []):
    print(f"  {r}")

print("\n=== CONTENT DESCRIPTIONS (first 15) ===")
for d in features.get("content_descriptions", [])[:15]:
    print(f"  {d}")

print("\n=== UI STRINGS (first 15) ===")
for s in features["ui_strings"][:15]:
    print(f"  {s}")
print(f"Total UI strings: {len(features['ui_strings'])}")

print("\n=== ACTIVITIES ===")
print(f"  {features['activities']}")

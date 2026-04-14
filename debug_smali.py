"""Debug script to see what top-level packages exist in each smali dir."""
import os, glob

base = r"C:\Users\Kareem Essam\AppData\Local\Temp\apk_decode_rgpua830"

for smali_dir in sorted(glob.glob(os.path.join(base, "smali*"))):
    name = os.path.basename(smali_dir)
    top_dirs = set()
    for f in glob.glob(os.path.join(smali_dir, "*")):
        top_dirs.add(os.path.basename(f))
    print(f"\n{name}: {sorted(top_dirs)}")

# Now find where NIA app classes live
print("\n\n=== NIA app classes location ===")
for smali_dir in sorted(glob.glob(os.path.join(base, "smali*"))):
    nia_path = os.path.join(smali_dir, "com", "google", "samples")
    if os.path.exists(nia_path):
        count = len(glob.glob(os.path.join(nia_path, "**", "*.smali"), recursive=True))
        print(f"  {os.path.basename(smali_dir)}: {count} NIA .smali files")

# Check what's in the first smali dir that ISN'T library code
print("\n\n=== Non-library classes in smali/ (first 20) ===")
smali_root = os.path.join(base, "smali")
skip = ("android/", "java/", "javax/", "kotlin/", "kotlinx/", "com/google/android/",
        "com/google/firebase/", "com/google/protobuf/", "com/google/common/",
        "com/google/gson/", "com/facebook/", "okhttp3/", "retrofit2/",
        "io/reactivex/", "androidx/", "dagger/", "hilt_aggregated_deps/",
        "org/intellij/", "org/jetbrains/")
count = 0
for f in sorted(glob.glob(os.path.join(smali_root, "**", "*.smali"), recursive=True)):
    rel = os.path.relpath(f, smali_root).replace(os.sep, "/").replace(".smali", "")
    if not any(rel.startswith(p) for p in skip):
        if count < 30:
            print(f"  {rel}")
        count += 1
print(f"  ... total: {count}")

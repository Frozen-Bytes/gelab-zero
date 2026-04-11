"""
CORE/ANALYZER/PARSER.PY
This module performs static analysis on a decompiled Android project.
It extracts metadata, UI text, and code signatures without actually running the app.
"""

import os
import re
import glob
import xml.etree.ElementTree as ET
from utils.logger import setup_logger

logger = setup_logger("parser")

# Constants from your code
_NOISE_STRINGS = {
    "ok", "cancel", "yes", "no", "back", "next", "done", "close",
    "app_name", "loading", "error", "retry", "submit", "save",
    "true", "false", "null", "",
}

_NOISE_PATTERNS = re.compile(
    r"^[\d\s\W]+$"  # pure numbers/symbols
    r"|^https?://"  # URLs
    r"|^[a-z0-9_]+$"  # raw keys like "ic_launcher"
    r"|%[sd]",  # format strings
    re.IGNORECASE,
)

_SMALI_SKIP_PREFIXES = (
    "android/", "java/", "javax/", "kotlin/", "com/google/",
    "com/facebook/", "okhttp3/", "retrofit2/", "io/reactivex/", "androidx/",
)

_INTERESTING_SUFFIXES = re.compile(
    r"(Activity|Fragment|Screen|Page|View|Manager|Service|Handler|"
    r"Repository|ViewModel|Controller|Helper|Utils?)$"
)

_METHOD_PATTERNS = re.compile(r"^\.(method|invoke).*?([a-z][a-zA-Z]+)\(", re.MULTILINE)

def parse_manifest(apk_dir: str) -> dict:
    """
    Parses 'AndroidManifest.xml'
    Extracts:
    - Package Name: The unique ID of the app.
    - Permissions: What the app is allowed to do (Camera, GPS, Internet).
    - Activities: The different 'Screens' the app contains.
    - Intent Actions: How the app communicates with other apps.
    """
    
    logger.info(f"Parsing manifest in: {apk_dir}")
    manifest_path = os.path.join(apk_dir, "AndroidManifest.xml")
    if not os.path.exists(manifest_path):
        logger.error("AndroidManifest.xml not found!")
        return {}

    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"XML Parse Error: {e}")
        return {}

    ns = "http://schemas.android.com/apk/res/android"
    package = root.attrib.get("package", "")

    activities = []
    for activity in root.iter("activity"):
        name = activity.attrib.get(f"{{{ns}}}name", "")
        if name:
            activities.append(name.split(".")[-1])

    permissions = []
    for perm in root.iter("uses-permission"):
        name = perm.attrib.get(f"{{{ns}}}name", "")
        if name:
            permissions.append(name.split(".")[-1])

    intent_actions = []
    for action in root.iter("action"):
        name = action.attrib.get(f"{{{ns}}}name", "")
        if name and not name.startswith("android.intent.action.MAIN"):
            intent_actions.append(name.split(".")[-1])

    logger.debug(f"Manifest parse complete for {package}")
    return {
        "package": package,
        "activities": list(dict.fromkeys(activities)),
        "permissions": list(dict.fromkeys(permissions)),
        "intent_actions": list(dict.fromkeys(intent_actions)),
    }

def parse_strings(apk_dir: str, max_strings: int = 60) -> list[str]:
    """
    Parses 'res/values/strings.xml' (The App's Vocabulary).
    This is where we find button labels, menu items, and titles.
    This gives the AI the best 'hints' about what the app actually does.
    """

    logger.info("Extracting UI strings...")
    strings_path = os.path.join(apk_dir, "res", "values", "strings.xml")
    if not os.path.exists(strings_path):
        return []

    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
    except ET.ParseError:
        return []

    labels = []
    for elem in root.iter("string"):
        text = (elem.text or "").strip()
        if text.lower() in _NOISE_STRINGS or _NOISE_PATTERNS.search(text):
            continue
        if 3 <= len(text) <= 80:
            labels.append(text)

    for elem in root.iter("item"):
        text = (elem.text or "").strip()
        if text and text.lower() not in _NOISE_STRINGS and 3 < len(text) < 80:
            if not _NOISE_PATTERNS.search(text):
                labels.append(text)

    unique = []
    seen = set()
    for s in labels:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    logger.debug(f"Found {len(unique)} unique strings")
    return unique[:max_strings]

def parse_smali(apk_dir: str, max_classes: int = 40) -> dict:
    """
    Scans '.smali' files
    Smali is the human-readable version of the app's compiled code.
    By looking at class names and method names, we can guess the app's logic.
    Example: Finding a method called 'uploadPhoto()' is a huge clue for the AI.
    """

    logger.info("Scanning smali files...")
    candidates = glob.glob(os.path.join(apk_dir, "smali*"))
    if not candidates:
        return {"classes": [], "methods": []}
    
    smali_root = candidates[0]
    class_names, method_names = [], []
    smali_files = glob.glob(os.path.join(smali_root, "**", "*.smali"), recursive=True)

    for path in smali_files:
        rel = os.path.relpath(path, smali_root)
        class_path = rel.replace(os.sep, "/").replace(".smali", "")
        if any(class_path.startswith(p) for p in _SMALI_SKIP_PREFIXES):
            continue

        class_short = class_path.split("/")[-1]
        if _INTERESTING_SUFFIXES.search(class_short) or (len(class_short) > 4 and not re.match(r"^[A-Z][0-9a-z]+$", class_short)):
            class_names.append(class_short)

        if len(method_names) < 80:
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read()
                for match in _METHOD_PATTERNS.finditer(content):
                    m = match.group(2)
                    if len(m) > 4 and m not in {"invoke", "method"}:
                        method_names.append(m)
            except Exception:
                pass

    return {
        "classes": list(dict.fromkeys(class_names))[:max_classes],
        "methods": list(dict.fromkeys(method_names))[:50]
    }
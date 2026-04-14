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

# ─── String noise filters ────────────────────────────────────────────

_NOISE_STRINGS = {
    "ok", "cancel", "yes", "no", "back", "next", "done", "close",
    "app_name", "loading", "error", "retry", "submit", "save",
    "true", "false", "null", "",
}

_NOISE_PATTERNS = re.compile(
    r"^[\d\s\W]+$"           # pure numbers/symbols
    r"|^https?://"           # URLs
    r"|^[a-z0-9_]+$"        # raw keys like "ic_launcher"
    r"|%[sd]"               # format strings
    r"|^@[a-z]+/"           # resource references like @dimen/..., @color/...
    r"|^#[0-9a-fA-F]{3,8}$" # hex color codes
    r"|^\?"                  # theme attribute references (?attr/, ?colorControlActivated, etc.)
    r"|^res/"                # resource path references
    r"|\\n"                  # strings that are just newlines
    r"|^[A-Z_]{2,}$",       # ALL_CAPS constants
    re.IGNORECASE,
)

# ─── Smali class/method filters ──────────────────────────────────────

_INTERESTING_SUFFIXES = re.compile(
    r"(Activity|Fragment|Screen|Page|View|Manager|Service|Handler|"
    r"Repository|ViewModel|Controller|Helper|Utils?|Composable|"
    r"Route|Navigation|Component|Module|UseCase|Interactor|DataSource|"
    r"Worker|Adapter|Provider|Dao|Database|Store|State|Event|Effect|"
    r"Dialog|Sheet|Layout|Widget|Bar|Button|Card|List|Grid|Panel|"
    r"Client|Api|Endpoint|Interceptor|Converter|Serializer|"
    r"Mapper|Transformer|Validator|Resolver|Delegate|Callback|Listener)$"
)

# Match .method declarations in smali
_METHOD_PATTERNS = re.compile(
    r"^\.method\s+.*?\s([a-zA-Z][a-zA-Z0-9_]{3,})\(",
    re.MULTILINE,
)

# Methods that are just boilerplate / auto-generated — skip these
_BORING_METHODS = {
    "invoke", "method", "equals", "hashCode", "toString",
    "valueOf", "values", "clone", "finalize", "getClass",
    "notify", "notifyAll", "access", "write", "writeTo",
    "describeContents", "createFromParcel", "newArray",
    "iterator", "compareTo", "compare", "apply",
    "accept", "getOrDefault", "forEach", "entrySet",
    "keySet", "containsKey", "contains", "isEmpty",
    "close", "flush", "reset", "clear",
}

# Class-name patterns to always skip (generated/synthetic noise)
_JUNK_CLASS_PATTERNS = re.compile(
    r"\$\d+$"                              # anonymous inner classes: Foo$1
    r"|\$\$ExternalSynthetic"              # D8 desugaring stubs
    r"|\$-CC$"                             # default-method companion classes
    r"|^ComposableSingletons\$"            # Compose compiler singletons
    r"|^HiltWrapper_"                      # Hilt wrapper classes
    r"|^Hilt_"                             # Hilt generated base classes
    r"|\$Companion$"                       # Kotlin companion objects
    r"|_(Factory|MembersInjector|Impl|Proxy|Stub|Module|"
    r"HiltModules|GeneratedInjector|Builder)$"  # Hilt/Dagger generated
    r"|^R$|^R\$"                           # R / R$drawable etc.
    r"|^BuildConfig$"                      # BuildConfig
    r"|^\$\$"                              # synthetic classes
    r"|\$\$inlined\$"                      # Kotlin inlined lambdas
    r"|\$\$serializer$"                    # kotlinx.serialization generated
)


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

def parse_strings(apk_dir: str, max_strings: int = 500) -> list[str]:
    """
    Parses string resources from the decompiled APK.
    Looks at:
      - res/values/strings.xml  (classic string resources)
      - All other res/values/*.xml files (string-arrays, plurals, etc.)
    This gives the AI the best 'hints' about what the app actually does.
    """

    logger.info("Extracting UI strings...")
    
    # Collect from ALL values XML files, not just strings.xml
    xml_files = glob.glob(os.path.join(apk_dir, "res", "values", "*.xml"))
    if not xml_files:
        return []

    labels = []
    for xml_path in xml_files:
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError:
            continue

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

    logger.info(f"Found {len(unique)} unique UI strings from {len(xml_files)} XML files")
    return unique[:max_strings]


def _discover_app_prefix(app_package: str, smali_dirs: list[str]) -> str:
    """
    Find the real smali path prefix for the app's own code.
    
    The manifest package often includes build-variant suffixes
    (e.g. "com.example.app.debug" or "com.google.samples.apps.nia.demo.debug")
    that don't correspond to actual source directories. We try the full package,
    then progressively strip the last segment until we find a directory that
    actually contains .smali files in at least one smali_classes* dir.
    
    Returns the prefix as a path with trailing slash, e.g. "com/example/app/".
    """
    if not app_package:
        return ""

    segments = app_package.split(".")
    
    # Try from full package down to at least 2 segments (e.g. "com/example/")
    for end in range(len(segments), 1, -1):
        candidate = "/".join(segments[:end])
        # Check if this path exists in any smali directory
        for smali_dir in smali_dirs:
            candidate_path = os.path.join(smali_dir, candidate.replace("/", os.sep))
            if os.path.isdir(candidate_path):
                # Verify it actually has .smali files (not just subdirs)
                has_smali = any(
                    f.endswith(".smali")
                    for f in os.listdir(candidate_path)
                ) or any(
                    os.path.isdir(os.path.join(candidate_path, d))
                    for d in os.listdir(candidate_path)
                )
                if has_smali:
                    prefix = candidate + "/"
                    if prefix != "/".join(segments) + "/":
                        logger.info(
                            f"Manifest package '{app_package}' trimmed to "
                            f"'{'.'.join(segments[:end])}' (build-variant suffix stripped)"
                        )
                    return prefix

    # Fallback: just use the full package
    return app_package.replace(".", "/") + "/"


def parse_smali(apk_dir: str, max_classes: int = 300, app_package: str = "") -> dict:
    """
    Scans '.smali' files across ALL dex directories (smali, smali_classes2, …).
    
    Uses a GENERIC strategy based on the app's package name:
      - Classes inside the app package → always included
      - Classes outside the app package → only included if they match
        the _INTERESTING_SUFFIXES pattern (known architectural names)
    
    This avoids maintaining a hardcoded list of every possible library.
    """

    logger.info("Scanning smali files...")
    # Scan ALL smali directories (multi-dex)
    smali_dirs = sorted(glob.glob(os.path.join(apk_dir, "smali*")))
    if not smali_dirs:
        return {"classes": [], "methods": [], "navigation_routes": [], "content_descriptions": []}
    
    logger.info(f"Found {len(smali_dirs)} smali directories: "
                f"{[os.path.basename(d) for d in smali_dirs]}")

    # Auto-discover the real app package prefix.
    # The manifest package often has build-variant suffixes (e.g. ".demo.debug")
    # that don't exist as directories in smali. We try the full package first,
    # then progressively strip segments until we find actual code.
    app_prefix = _discover_app_prefix(app_package, smali_dirs)
    logger.info(f"App package prefix: '{app_prefix or '(unknown)'}'")
    
    app_classes = []
    app_methods = []
    external_classes = []  # interesting classes outside the app package
    nav_routes = []
    content_descriptions = []

    # Compose navigation/screen detection from class names
    screen_class_pattern = re.compile(
        r"(Screen|Route|Destination|Navigation|NavGraph|TopLevel|Tab)"
    )

    for smali_root in smali_dirs:
        smali_files = glob.glob(
            os.path.join(smali_root, "**", "*.smali"), recursive=True
        )
        logger.debug(f"  {os.path.basename(smali_root)}: {len(smali_files)} .smali files")

        for path in smali_files:
            rel = os.path.relpath(path, smali_root)
            class_path = rel.replace(os.sep, "/").replace(".smali", "")
            class_short = class_path.split("/")[-1]

            # Skip junk/generated class names
            if _JUNK_CLASS_PATTERNS.search(class_short):
                continue

            is_app_class = bool(app_prefix and class_path.startswith(app_prefix))

            if is_app_class:
                # ── APP CODE: include if it has a meaningful name ──
                if len(class_short) > 3 and not re.match(r"^[A-Z][0-9a-z]+$", class_short):
                    app_classes.append(class_short)

                # Read file for methods, routes, content descriptions
                try:
                    with open(path, "r", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue

                # Extract method names from app code only
                for match in _METHOD_PATTERNS.finditer(content):
                    m = match.group(1)
                    if m not in _BORING_METHODS:
                        app_methods.append(m)

                # Detect Compose screen names from class naming
                if screen_class_pattern.search(class_short):
                    # The class name itself is a meaningful screen/route identifier
                    nav_routes.append(class_short)

                # Look for content descriptions (Compose semantics)
                if "ContentDescription" in content or "contentDescription" in content:
                    for match in re.finditer(
                        r'const-string\s+[vp]\d+,\s+"([A-Z][a-zA-Z ]{3,40})"',
                        content,
                    ):
                        desc = match.group(1)
                        if desc not in {"Null", "True", "False", "String", "Object"}:
                            content_descriptions.append(desc)

            else:
                # ── EXTERNAL CODE: only include if it has an architectural suffix ──
                if _INTERESTING_SUFFIXES.search(class_short):
                    external_classes.append(class_short)

    # Deduplicate everything
    unique_app_classes = list(dict.fromkeys(app_classes))
    unique_ext_classes = list(dict.fromkeys(external_classes))
    unique_methods = list(dict.fromkeys(app_methods))
    unique_routes = list(dict.fromkeys(nav_routes))
    unique_descs = list(dict.fromkeys(content_descriptions))

    # Combine: app classes first (most important), then external with suffix
    all_classes = unique_app_classes[:max_classes]
    remaining_slots = max_classes - len(all_classes)
    if remaining_slots > 0:
        all_classes.extend(unique_ext_classes[:remaining_slots])

    logger.info(
        f"Smali scan complete: "
        f"{len(unique_app_classes)} app classes, "
        f"{len(unique_ext_classes)} external classes, "
        f"{len(unique_methods)} methods, "
        f"{len(unique_routes)} nav routes, "
        f"{len(unique_descs)} content descriptions"
    )

    return {
        "methods": unique_methods[:300],
        "navigation_routes": unique_routes,
        "content_descriptions": unique_descs[:200],
    }
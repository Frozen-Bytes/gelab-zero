"""
UTILS/APK_UTILS.PY
This module handles APK decoding and optional device interaction.
"""

import os
import shutil
import subprocess
import tempfile
from utils.logger import setup_logger

logger = setup_logger("apk_utils")


def validate_apk_path(apk_path: str) -> None:
    if not apk_path:
        raise ValueError("APK path is required.")

    if not os.path.exists(apk_path):
        raise FileNotFoundError(f"APK not found: {apk_path}")

    if not apk_path.lower().endswith(".apk"):
        raise ValueError(f"File does not appear to be an APK: {apk_path}")


def prepare_output_dir(output_dir: str | None) -> str:
    if output_dir:
        return os.path.abspath(output_dir)
    return tempfile.mkdtemp(prefix="apk_decode_")


def decode_apk(apk_path: str, output_dir: str) -> str:
    """
    Uses apktool to decode an APK into a readable folder structure.

    Args:
        apk_path (str): Path to the APK file.
        output_dir (str): Destination folder for the decoded contents.

    Returns:
        str: The folder path containing decoded APK files.

    Raises:
        RuntimeError: If apktool fails or the decode cannot complete.
    """

    if os.path.exists(output_dir):
        manifest_path = os.path.join(output_dir, "AndroidManifest.xml")
        if os.path.exists(manifest_path):
            logger.info(f"Directory '{output_dir}' already exists and appears decoded. Skipping decode.")
            return output_dir
        else:
            logger.info(f"Directory '{output_dir}' exists but is incomplete. Removing and re-decoding.")
            shutil.rmtree(output_dir)

    os.makedirs(os.path.dirname(output_dir), exist_ok=True)
    logger.info(f"Decoding APK: {apk_path} ... this may take few minutes, if nothing happen try pressing on the keyboard")

    result = subprocess.run(
        ["apktool", "d", apk_path, "-o", output_dir, "--force"],
        capture_output=True,
        text=True,
        shell=True,
    )

    if result.returncode != 0:
        logger.error(f"apktool error: {result.stderr.strip()}")
        raise RuntimeError("APK decoding failed. Ensure apktool is installed and on your PATH.")

    logger.info(f"Decoded successfully to: {output_dir}")
    return output_dir


def run_adb_command(adb_serial, args, timeout=180):
    command = ["adb"]
    if adb_serial:
        command += ["-s", adb_serial]
    command += args

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ADB command failed ({command}): {result.stderr.strip()}")

    return result


def ensure_device_connected(adb_serial):
    result = run_adb_command(adb_serial, ["devices"])
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    lines = [line for line in lines if not line.startswith("List of devices")]

    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, status = parts[0], parts[1]
        if serial == adb_serial and status == "device":
            logger.info(f"Device {adb_serial} is connected and ready")
            return

    raise RuntimeError(f"No connected device found for serial {adb_serial}. adb devices output:\n{result.stdout}")


def install_apk_on_device(adb_serial, apk_path):
    logger.info(f"Installing APK on device {adb_serial}...")
    run_adb_command(adb_serial, ["install", "-r", apk_path])
    logger.info("APK install completed.")


def reset_app(adb_serial, package_name):
    if not package_name:
        raise ValueError("package_name is required")

    base_cmd = ["adb"]
    if adb_serial:
        base_cmd += ["-s", adb_serial]

    subprocess.run(
        base_cmd + ["shell", "am", "force-stop", package_name],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    subprocess.run(
        base_cmd + [
            "shell",
            "monkey",
            "-p",
            package_name,
            "-c",
            "android.intent.category.LAUNCHER",
            "1",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    logger.info(f"Reset app: {package_name}")

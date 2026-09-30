import logging
import subprocess
import time
from pathlib import Path

import requests

from otp_mobility.utils.config import OTP_URL

logger = logging.getLogger(__name__)


def start_otp_with_log(
    folder_data_path, 
    folder_jar_path, 
    log_path
):
    """Start OTP and append its stdout/stderr to an external log file."""
    jar_path = Path(folder_jar_path).expanduser().resolve()
    command = [
        "java",
        "-Xmx2G",
        "-jar",
        str(jar_path),
        "--build",
        "--serve",
        str(folder_data_path),
    ]
    log_file = open(log_path, "a", encoding="utf-8", buffering=1)
    process = subprocess.Popen(
        command,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, log_file


def start_otp(
    folder_data_path,
    folder_jar_path,
):
    """Start OTP and without saving stdout/stderr."""
    folder_jar_extended = Path(folder_jar_path).expanduser().resolve()
    command = [
        "java",
        "-Xmx2G",
        "-jar",
        str(folder_jar_extended),
        "--build",
        "--serve",
        str(folder_data_path),
    ]

    logger.info("Starting OpenTripPlanner...")
    logger.debug("Command: %s", " ".join(command))

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    return process


def wait_for_otp(process, timeout=600):
    """
    Wait until OTP responds.
    timeout is expressed in seconds.
    """

    start_time = time.time()

    logger.info("Waiting for OTP to become ready...")
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            log_text = ""
            if process.stdout is not None:
                try:
                    log_text = process.stdout.read()
                except Exception:
                    log_text = ""

            if log_text.strip():
                logger.error("OTP exited early. Captured logs:\n%s", log_text)
                raise RuntimeError(
                    f"OTP stopped with exit code {process.returncode}.\n"
                    f"Captured logs:\n{log_text}"
                )

            raise RuntimeError(
                f"OTP stopped with exit code {process.returncode}"
            )

        try:
            response = requests.get(
                f"{OTP_URL}/",
                timeout=2,
            )

            if response.status_code < 500:
                logger.info("OTP is ready!")
                return

        except requests.RequestException:
            pass

        time.sleep(2)

    raise TimeoutError("OTP was not available before the timeout elapsed")


def stop_otp(process):
    logger.info("Stopping OTP...")

    process.terminate()

    try:
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        logger.warning("OTP did not stop cleanly; terminating forcefully...")
        process.kill()

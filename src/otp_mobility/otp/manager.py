import logging
import subprocess
import time
from pathlib import Path

import requests

from otp_mobility.utils.config import OTP_URL

logger = logging.getLogger(__name__)


def start_otp(
    folder_data_path,
    folder_jar_path,
):
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

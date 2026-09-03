import logging
import os

OTP_ENDPOINT = "http://localhost:8080/otp/routers/default/index/graphql"
OTP_URL = "http://localhost:8080"

PROJECT = "test-otp-v2"

_level_name = os.environ.get("BDT_LOG_LEVEL", "INFO").upper()
logging_level = getattr(logging, _level_name, logging.INFO)

logging.basicConfig(
	level=logging_level,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# src/cron/keep_alive.py

import os
import time
import requests
import logging

logger = logging.getLogger(__name__)

def keep_alive_job():
    url = os.getenv("API_URL")
    if not url:
        logger.error("API_URL environment variable not set. Skipping keep-alive.")
        return

    def send_keep_alive():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info("Keep-alive request sent successfully", extra={
                    "url": url,
                    "status_code": response.status_code,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
                })
                return True
            else:
                logger.error("Keep-alive request failed", extra={
                    "url": url,
                    "status_code": response.status_code,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
                })
                raise ValueError(f"Status code: {response.status_code}")
        except Exception as e:
            logger.error("Error while sending keep-alive request", extra={
                "url": url,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
            })
            raise

    max_retries = 3
    for i in range(max_retries):
        try:
            send_keep_alive()
            break
        except Exception as e:
            if i < max_retries - 1:
                logger.info(f"Retrying keep-alive request ({i + 2}/{max_retries}) in 5 seconds...")
                time.sleep(5)
            else:
                logger.error("Keep-alive request failed after max retries", extra={
                    "url": url,
                    "error": str(e)
                })
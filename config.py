import os
import json

from logger import logger

TELEGRAM_TOKEN = "6994059390:AAFkwBKlwC4dOlHQJQMozGlxw2oYO28ePOc"
TELEGRAM_ADMINS = json.loads(os.getenv("TELEGRAM_ADMINS", "[6113190687]"))

logger.info("admins: " + str(json.loads(os.getenv("TELEGRAM_ADMINS", "[6113190687]"))))

API_KEY = "411af5ed-44b5-49a6-b018-f8fd98322ff4"

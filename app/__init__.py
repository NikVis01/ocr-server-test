import logging

# Ensure our app logs show up even if the host doesn't configure logging.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

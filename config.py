# Tracker Configuration

# PROJECT CONFIG
PROJECT_NAME = "Example Tracker" # E.g. "LAION-5B", "Crawling@Home", ...
STAGE_A = "CPU"
STAGE_B = "GPU"
STAGE_C = None
STAGE_D = None
STAGE_E = None

# DATABASE CONFIG
SQL_CONN_URL = "postgres:///exampletracker" # Example config for a postgres database. Works with any databases supported by Tortoise ORM.
REDIS_CONN_URL = "redis://127.0.0.1" # The Redis connection URL, used for caching webpages to avoid database strain.

# WORKER CONFIG
IDLE_TIMEOUT = 7200 # The interval, in seconds, until a worker is kicked for being idle. (default 2 hours)

# ETA CALCULATION
AVERAGE_INTERVAL = 900 # The interval for each measurement of the averages to take place. (default 15 minutes)
AVERAGE_DATASET_LENGTH = 10 # The sample size for computing worker speed.

# CACHE
PAGE_CACHE_EXPIRY = 30 # The number of seconds until the page cache is cleared and the page is re-rendered. (avoids database strain)
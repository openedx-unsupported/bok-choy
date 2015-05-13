"""
bok-choy is a UI-level acceptance test framework
"""
import logging

# Suppress noisy loggers
NOISY_LOGGERS = ['selenium.webdriver.remote.remote_connection', 'paramiko.transport']
for log_name in NOISY_LOGGERS:
    logging.getLogger(log_name).setLevel(logging.WARNING)

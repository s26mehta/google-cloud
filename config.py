"""
Name: Configuration for this repository

Purpose: Storage globally used variables, create logging service and provide google cloud storage credentials
"""

import logging
import json

from httplib2 import Http
from logging import handlers
from oauth2client.service_account import ServiceAccountCredentials

# ------------###############################--------------- #
# Uncomment next line and comment out line 12 if you are using older version of oauth2client
# from oauth2client.client import SignedJwtAssertionCredentials


PROJECT_NAME = ''    # This is the project name you chose
NETWORK_NAME = ''    # This is the network name you chose for your project
STORAGE_ZONE = ''    # This is the zone your google cloud storage bucket resides in
STORAGE_BUCKET = ''  # This is the name of the bucket that want to upload files to
STORAGE_KEY = ''     # This will be the google cloud storage key file in json format


# Create logging service
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

# Create handler to output log to new file daily
LOG_FILENAME = 'logs/upload_log'
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when='midnight')

# Create formatter for logging and add to logger
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_client_email_from_json():
    """
    Get the Client Email from JSON storage
    :return: Client Email
    """
    try:
        with open(STORAGE_KEY) as data:
            client_email = json.load(data)
        return client_email['client_email']

    except Exception as e:
        logger.debug("Unable to get client email for credentials: %s" % e)
        return None


def get_private_key_from_json():
    """
    Gets the private key from JSON storage
    :return: Private Key
    """
    try:
        with open(STORAGE_KEY) as data:
            private_key = json.load(data)
        return private_key['private_key']

    except Exception as e:
        logger.debug("Unable to get private key for credentials: %s" % e)
        return None


def get_storage_credentials():
    """
    Get the Google Cloud Storage Credentials
    :return: Google Cloud Credentials
    """
    try:
        # ------------###############################---------------#
        # Uncomment next few line and comment out line 75 if you are using older version of oauth2client
        # client_email = get_client_email_from_json()
        # private_key = get_private_key_from_json()
        # credentials = SignedJwtAssertionCredentials(client_email, private_key,

        credentials = ServiceAccountCredentials.from_json_keyfile_name(STORAGE_KEY,
                                                                'https://www.googleapis.com/auth/devstorage.read_write')
        credentials.authorize(Http())
        return credentials

    except Exception as e:
        logger.debug("Unable to get credentials: %s" % e)
        return None


def get_compute_engine_credentials():
    """
    Get the Google Cloud Storage Credentials
    :return: Google Cloud Credentials
    """
    try:
        client_email = get_client_email_from_json()
        private_key = get_private_key_from_json()
        credentials = SignedJwtAssertionCredentials(client_email, private_key,
                                                    'https://www.googleapis.com/auth/compute')
        return credentials
    except Exception as e:
        logger.debug("Unable to get credentials: %s" % e)
        return None

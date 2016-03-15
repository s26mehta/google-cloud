"""
Name: Google Cloud Storage Download

Purpose: Download Files from a google cloud storage bucket
"""

import io
import time
import apiclient

from config import logger, STORAGE_BUCKET, get_storage_credentials
from apiclient import discovery


CHUNK_SIZE = 1024 * 2 * 2


def download_file_from_storage(file_name, local_path, bucket=STORAGE_BUCKET):
    """
    Download a file from the Google Cloud storage
    :param file_name: The name of the file on google cloud storage (include extension!)
    :param local_path: The local path to save the downloaded file to
    :param bucket: The bucket on Cloud
    :return: True if successful, False otherwise ---- if download of entire database, list of
                                                      datasets, with total size (last item) is returned
    """
    try:
        logger.info("Downloading file named %s from google cloud" % file_name)
        service = discovery.build('storage', 'v1', credentials=get_storage_credentials())

        req = service.objects().get_media(bucket=bucket, object=file_name)

        check = local_path.endswith('/')
        if check is not True:
            local_path = local_path + '/'

        fh = io.FileIO(local_path+file_name, mode='wb')
        downloader = apiclient.http.MediaIoBaseDownload(fh, req, chunksize=CHUNK_SIZE)
        done = False

        start = time.time()
        while not done:
            status, done = downloader.next_chunk()
            if status:
                logger.info('Download %d%%.' % int(status.progress() * 100))
        end = time.time()

        logger.info("Download completed!")
        logger.info("Time to download: %d (sec)" % (end-start))

        return True

    except Exception as e:
        logger.debug("Download Failed: %s" % e)
        return False

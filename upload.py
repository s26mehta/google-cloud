"""
Name: Upload to google cloud storage

Purpose: Upload files to google cloud storage buckets
"""

from apiclient import discovery
from config import logger, STORAGE_BUCKET, get_storage_credentials


def upload_file(local_path, remote_name, bucket=STORAGE_BUCKET):
    """
    Upload a file to Google Storage
    :param local_path: The local path to the file to upload
    :param remote_name: The name of the file in the google cloud storage
    :param bucket: The bucket on google cloud storage you want to upload the file to
    :return: True if uploaded, False otherwise
    """
    try:
        service = discovery.build('storage', 'v1', credentials=get_storage_credentials())
        logger.info("Uploading %s to google cloud" % local_path)
        req = service.objects().insert(
            bucket=bucket,
            name=remote_name,
            # predefinedAcl="publicRead",         Uncomment this line if you want your files to be accessible to anyone
            media_body=local_path)
        req.execute()
        logger.info("Upload complete!")

        uploaded = check_if_file_exists(remote_name)

        if uploaded is True:
            return True
        else:
            return False

    except Exception as e:
        logger.debug("Unable to upload file %s to google cloud: %s" % (local_path, e))
        return False


def check_if_file_exists(name, bucket=STORAGE_BUCKET):
    """
    Check if file exists on google cloud storage
    :param name: Name of file you are checking
    :param bucket: Bucket where you expect the file to be
    :return: True if exists. False otherwise
    """
    try:
        service = discovery.build('storage', 'v1', credentials=get_storage_credentials())

        request = service.objects().get(bucket=bucket, object=name)
        request.execute()

        return True

    except FileNotFoundError:
        logger.debug("Image %s does not exist on google cloud" % name)
        return False

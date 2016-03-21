"""
Name: VM manager

Date Created: January 25, 2016

Created By:
    Shubam Mehta

Purpose: Create, start, terminate and delete google cloud virtual machines via this script

"""

# Installing python on vm:
# mkdir test
# cd test/
# wget https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tgz
# tar -xvf Python-3.5.1.tgz
# cd Python-3.5.1/
# apt-get install build-essential
# ./configure
# make install


import json
import time

from config import logger, PROJECT_NAME, get_storage_credentials
from apiclient import discovery

DEFAULT_VM_ZONE = "us-central1-f"


def list_vm_instances(project=PROJECT_NAME, zone=DEFAULT_VM_ZONE):
    try:
        compute = discovery.build('compute', 'v1', credentials=get_storage_credentials())
        req = compute.instances().list(project=project, zone=zone)
        response = req.execute()
        print(json.dumps(response['items'], indent='\n'))
        return response

    except Exception as e:
        logger.debug("Unable to list instances: %s" % e)


def create_disk_for_vm(name, source_image, disk_size, zone=DEFAULT_VM_ZONE, project=PROJECT_NAME):
    """
    Creates disk on Google Cloud compute engine to be used alongside a vm. Disk is generated from
    an image that is also stored on Google Cloud compute engine

    :param name: Name of disk (Usually same name as VM_name)
    :param source_image: Image for disk to replicate (stored on google cloud compute engine/ images)
    :param disk_size: Size of disk
    :param zone: The zone the disk should be created in (same as VM zone)
    :param project: Name of project
    :return: Link of disk if successful, False if unsuccessful
    """
    try:
        compute = discovery.build('compute', 'v1', credentials=get_storage_credentials())

        config = {
            'name': name,
            'description': '',
            'sizeGb': disk_size,
            'sourceImage': source_image,
        }

        req = compute.disks().insert(project=project, zone=zone, body=config)
        resp = req.execute()

        completed = wait_for_operation(project, zone, resp['name'])

        if completed == 'DONE':
            link = resp['targetLink'].split('/v1/')[1]
            return link

    except Exception as e:
        logger.debug("Creation of disk failed: %s" % e)
        print(e)
        return False


def wait_for_operation(project, zone, operation):
    """
    Checks if operation demanded (create/start/stop/delete) is completed

    :param project: Project name on google cloud
    :param zone: zone the vm_instance resides in
    :param operation: which operation is being run
    :return: True when completed
    """
    logger.debug('Waiting for operation to finish...')

    while True:
        try:
            compute = discovery.build('compute', 'v1', credentials=get_storage_credentials())
            req = compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation
            )
            result = req.execute()

            if result['status'] == 'DONE':
                return result['status']

            time.sleep(1)
        except Exception as e:
            logger.debug('Checking if operation is completed failed: %s' % e)
